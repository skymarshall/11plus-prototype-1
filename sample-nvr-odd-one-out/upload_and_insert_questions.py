#!/usr/bin/env python3
"""
Script 2: Do all the rest (QUESTION-GENERATION-BATCH.md).

Reads manifest, uploads each question folder to storage, then inserts each question
and its 5 answer_options into the database.

Usage:
  python upload_and_insert_questions.py --manifest output/questions/manifest.json --dry-run
  python upload_and_insert_questions.py --manifest output/questions/manifest.json \\
    --base-url https://xxx.supabase.co/storage/v1/object/public/options \\
    --upload supabase --bucket options --subject-id 1 --topic-id 1 --database-url postgresql://...

What script 2 needs: manifest path, storage config (for upload), DB connection, subject/topic ids.
With --dry-run: only validates manifest and lists what would be uploaded/inserted.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_manifest(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _upload_supabase_s3(
    question_dir: Path,
    qid: str,
    bucket: str,
    prefix: str,
    base_url: str,
) -> str:
    """Upload via Supabase Storage S3-compatible API (use Access Key + Secret Key from supabase status)."""
    api_url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    s3_url = os.environ.get("SUPABASE_STORAGE_S3_URL") or f"{api_url}/storage/v1/s3"
    access = os.environ.get("SUPABASE_STORAGE_ACCESS_KEY")
    secret = os.environ.get("SUPABASE_STORAGE_SECRET_KEY")
    region = os.environ.get("SUPABASE_STORAGE_REGION", "local")
    if not access or not secret:
        raise SystemExit(
            "S3 upload requires SUPABASE_STORAGE_ACCESS_KEY and SUPABASE_STORAGE_SECRET_KEY from 'supabase status' (Storage section)."
        )
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        raise SystemExit("S3 upload requires boto3: pip install boto3")
    client = boto3.client(
        "s3",
        endpoint_url=s3_url,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=region,
        config=Config(signature_version="s3v4"),
    )
    folder_prefix = f"{prefix.rstrip('/')}/{qid}" if prefix else qid
    for f in question_dir.iterdir():
        if f.is_file() and f.suffix.lower() in (".svg", ".png", ".jpg", ".jpeg"):
            object_path = f"{folder_prefix}/{f.name}"
            data = f.read_bytes()
            content_type = "image/svg+xml" if f.suffix.lower() == ".svg" else "image/png"
            client.put_object(
                Bucket=bucket,
                Key=object_path,
                Body=data,
                ContentType=content_type,
            )
    return f"{base_url.rstrip('/')}/{qid}"


def _upload_supabase_rest(
    question_dir: Path,
    qid: str,
    bucket: str,
    prefix: str,
    base_url: str,
) -> str:
    """Upload via Supabase Storage REST API (requires service_role JWT, not sb_secret_ keys)."""
    api_url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    if not api_url or not key:
        raise SystemExit(
            "REST upload requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (JWT)."
        )
    folder_prefix = f"{prefix.rstrip('/')}/{qid}" if prefix else qid
    for f in question_dir.iterdir():
        if f.is_file() and f.suffix.lower() in (".svg", ".png", ".jpg", ".jpeg"):
            object_path = f"{folder_prefix}/{f.name}"
            data = f.read_bytes()
            content_type = "image/svg+xml" if f.suffix.lower() == ".svg" else "image/png"
            upload_url = f"{api_url}/storage/v1/object/{bucket}/{object_path}"
            req = urllib.request.Request(
                upload_url,
                data=data,
                headers={
                    "apikey": key,
                    "Authorization": f"Bearer {key}",
                    "Content-Type": content_type,
                    "x-upsert": "true",
                },
                method="POST",
            )
            try:
                urllib.request.urlopen(req)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace") if e.fp else ""
                msg = f"Storage upload failed {e.code} {upload_url}\n{body}"
                if "Invalid Compact JWS" in body or "403" in body:
                    msg += "\nUse S3 keys instead: set SUPABASE_STORAGE_ACCESS_KEY and SUPABASE_STORAGE_SECRET_KEY from 'supabase status' (Storage)."
                raise SystemExit(msg)
    return f"{base_url.rstrip('/')}/{qid}"


def _upload_supabase(
    question_dir: Path,
    qid: str,
    bucket: str,
    prefix: str,
    base_url: str,
) -> str:
    """Upload to Supabase Storage. Prefers S3 API when Storage keys are set (for local sb_secret_ setups)."""
    if os.environ.get("SUPABASE_STORAGE_ACCESS_KEY") and os.environ.get("SUPABASE_STORAGE_SECRET_KEY"):
        return _upload_supabase_s3(question_dir, qid, bucket, prefix, base_url)
    return _upload_supabase_rest(question_dir, qid, bucket, prefix, base_url)


def _insert_question_and_options(
    cursor,
    question: dict,
    base_url: str,
    subject_id: int,
    topic_id: int,
    question_type: str = "multiple_choice",
    points: int = 1,
    time_limit_seconds: int = 90,
) -> int:
    """Insert one question and its 5 answer_options. Return question id."""
    qid = question["id"]
    question_base_url = f"{base_url.rstrip('/')}/{qid}"
    question_text = question.get("question_text") or "Which shape is the odd one out?"
    explanation = question.get("explanation")
    correct_index = question["correct_index"]
    option_files = question.get("option_files", ["option-a.svg", "option-b.svg", "option-c.svg", "option-d.svg", "option-e.svg"])

    cursor.execute(
        """
        INSERT INTO questions (
            subject_id, topic_id, question_type, question_text,
            question_image_url, explanation, points, time_limit_seconds
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (subject_id, topic_id, question_type, question_text, None, explanation, points, time_limit_seconds),
    )
    row = cursor.fetchone()
    question_db_id = row[0]

    for order, filename in enumerate(option_files, start=1):
        option_url = f"{question_base_url}/{filename}"
        is_correct = order - 1 == correct_index
        cursor.execute(
            """
            INSERT INTO answer_options (question_id, option_text, option_image_url, is_correct, display_order)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (question_db_id, "", option_url, is_correct, order),
        )
    return question_db_id


def _lookup_nvr_subject_topic(cursor) -> tuple[int, int]:
    """Look up subject_id for code 'NVR' and topic_id for topic 'Shapes' (root) under that subject."""
    cursor.execute("SELECT id FROM subjects WHERE code = 'NVR'")
    row = cursor.fetchone()
    if not row:
        raise SystemExit("Subject with code 'NVR' not found. Run insert_nvr_subject_topic_supabase.sql first.")
    subject_id = row[0]
    cursor.execute(
        "SELECT id FROM topics WHERE subject_id = %s AND name = 'Shapes' AND parent_topic_id IS NULL",
        (subject_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise SystemExit("Topic 'Shapes' not found for subject NVR. Run insert_nvr_subject_topic_supabase.sql first.")
    topic_id = row[0]
    return subject_id, topic_id


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload question option images and insert questions + answer_options into the database."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        metavar="PATH",
        help="Path to manifest.json from script 1.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only validate manifest and print what would be done; no upload, no DB insert.",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        metavar="URL",
        help="Base URL for option images (e.g. https://xxx.supabase.co/storage/v1/object/public/options). Required unless --dry-run and no insert.",
    )
    parser.add_argument(
        "--upload",
        type=str,
        choices=["supabase", "skip"],
        default="skip",
        help="Upload option files: supabase (use SUPABASE_* env), or skip (you provide --base-url and upload elsewhere). Default: skip.",
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default="options",
        help="Storage bucket name (for supabase upload). Default: options.",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="",
        help="Path prefix inside bucket (e.g. questions). Default: empty.",
    )
    parser.add_argument(
        "--subject-id",
        type=int,
        default=None,
        metavar="ID",
        help="Subject id for questions. Default: lookup by code 'NVR'.",
    )
    parser.add_argument(
        "--topic-id",
        type=int,
        default=None,
        metavar="ID",
        help="Topic id for questions. Default: lookup topic 'Shapes' under NVR.",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=os.environ.get("DATABASE_URL"),
        metavar="URL",
        help="PostgreSQL connection URL (or set DATABASE_URL env).",
    )
    parser.add_argument(
        "--questions-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directory containing question subfolders (default: same dir as manifest).",
    )
    parser.add_argument(
        "--question-type",
        type=str,
        default="multiple_choice",
        help="question_type value. Default: multiple_choice.",
    )
    parser.add_argument(
        "--points",
        type=int,
        default=1,
        help="Points per question. Default: 1.",
    )
    parser.add_argument(
        "--time-limit-seconds",
        type=int,
        default=90,
        help="Time limit per question in seconds. Default: 90.",
    )
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    if not manifest_path.is_file():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    manifest = _load_manifest(manifest_path)
    questions = manifest.get("questions", [])
    base_dir_name = manifest.get("base_dir", "questions")
    if not questions:
        raise SystemExit("Manifest has no questions.")

    questions_dir = args.questions_dir or manifest_path.parent
    questions_dir = questions_dir.resolve()

    if args.dry_run:
        print("Dry run: no upload, no DB insert.")
        print(f"Manifest: {manifest_path} ({len(questions)} questions)")
        print(f"Questions dir: {questions_dir}")
        for q in questions:
            qid = q["id"]
            qdir = questions_dir / qid
            exists = qdir.is_dir()
            print(f"  {qid}: dir exists={exists}, correct_index={q.get('correct_index')}")
        return

    if not args.base_url:
        raise SystemExit("Without --dry-run, provide --base-url (or upload and we build it from storage).")
    base_url = args.base_url

    subject_id = args.subject_id if args.subject_id is not None else os.environ.get("SUBJECT_ID")
    topic_id = args.topic_id if args.topic_id is not None else os.environ.get("TOPIC_ID")
    if subject_id is not None:
        subject_id = int(subject_id)
    if topic_id is not None:
        topic_id = int(topic_id)

    # Upload if requested
    if args.upload == "supabase":
        if not base_url:
            raise SystemExit("With --upload supabase you must set --base-url to the bucket public URL.")
        for q in questions:
            qid = q["id"]
            qdir = questions_dir / qid
            if not qdir.is_dir():
                raise SystemExit(f"Question folder not found: {qdir}")
            print(f"Uploading {qid} … ", end="", flush=True)
            _upload_supabase(qdir, qid, args.bucket, args.prefix, base_url)
            print("ok")

    # DB insert
    if not args.database_url:
        print("No DATABASE_URL / --database-url; skipping insert.")
        return

    conn = None
    try:
        import psycopg2
        conn = psycopg2.connect(args.database_url)
    except ImportError:
        try:
            import pg8000
            from urllib.parse import urlparse
            u = urlparse(args.database_url)
            if u.scheme not in ("postgresql", "postgres"):
                raise SystemExit("DATABASE_URL must be postgresql://...")
            conn = pg8000.connect(
                host=u.hostname or "127.0.0.1",
                port=int(u.port or 5432),
                user=u.username or "postgres",
                password=u.password or "",
                database=(u.path or "/postgres").lstrip("/") or "postgres",
            )
        except ImportError:
            raise SystemExit(
                "DB insert requires a PostgreSQL driver. Install one:\n"
                "  pip install psycopg2-binary   (or)\n"
                "  pip install pg8000"
            )

    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            if subject_id is None or topic_id is None:
                subject_id, topic_id = _lookup_nvr_subject_topic(cur)
                print(f"Using subject_id={subject_id} (NVR), topic_id={topic_id} (Shapes)")
            for q in questions:
                qid = q["id"]
                q_db_id = _insert_question_and_options(
                    cur,
                    q,
                    base_url,
                    subject_id,
                    topic_id,
                    question_type=args.question_type,
                    points=args.points,
                    time_limit_seconds=args.time_limit_seconds,
                )
                print(f"Inserted {qid} -> questions.id={q_db_id}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise SystemExit(f"Insert failed: {e}") from e
    finally:
        conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
