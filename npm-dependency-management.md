# NPM Dependency Best Practice Notes
Date: February 10, 2026

This has **not** been implemented yet.

Currently, npm/npx must be run separately within
 - a separate Supabase instance directory (used to start/stop the database)
 - the 11-practise-hub UI directory (used to start/stop the webserver)

Python/Batch scripts are run from question-gen

TODO : Clean this up to use a single npm workspace from the root directory.

## Topic 1: Best Practices for npm Dependencies
* **Categorization:** Use `dependencies` for runtime and `devDependencies` for build-time tools.
* **Stability:** Always commit `package-lock.json` to ensure consistent environments.
* **CI/CD:** Use `npm ci` in pipelines instead of `npm install` for faster, cleaner builds.
* **Security:** Run `npm audit` regularly and consider disabling lifecycle scripts (`ignore-scripts`).
* **Maintenance:** Use `npm outdated` and tools like `depcheck` to keep the project lean.

---

## Topic 2: Project Structure (Monorepo vs. Single Root)
* **Single Root:** Best for simple applications where all code shares the same context.
* **Subdirectories (Workspaces):** Best for complex projects with distinct parts (e.g., UI, DB, Logic).
* **Recommendation:** Use **npm Workspaces** if parts of the project could theoretically be deployed separately. It allows for isolation while keeping management centralized.

---

## Topic 3: npx vs. npm
* **npm:** The "Toolbox." Used for installing and managing packages long-term.
* **npx:** The "Runner." Used to execute packages without permanent installation (great for one-off commands like `create-react-app`).
* **Workflow:** `npx` is smart enough to find binaries in your local `node_modules` or fetch them temporarily from the registry.

---

## Topic 4: npm Workspaces Deep Dive
* **Execution:** From the root, use `npm exec -w <workspace-name> -- <command>` to target a subdirectory.
* **Hoisting:** npm installs shared dependencies at the root level to save space and prevent version conflicts.
* **Configuration:** * Root `package.json` defines the `workspaces` array.
    * Each subdirectory has its own `package.json` with its own specific dependencies.

### Example Project Structure:
/root
├── package.json (defines workspaces)
├── 11-practise-hub (Vite UI)
│   └── package.json
├── supabase (DB scripts)
│   └── package.json
└── question-gen (Batch logic)
    └── package.json

---

## Topic 5: Sample Root package.json
{
  "name": "my-monorepo-project",
  "private": true, 
  "workspaces": [
    "11-practice-hub",
    "supabase",
    "question-gen"
  ],
  "scripts": {
    "ui:dev": "npm install <package-name> -w 11-practice-hub",
    "logic:run": "npm start -w question-gen",
    "db:status": "npx supabase status -w supabase",
    "install:all": "npm install",
    "test:all": "npm test -ws"
  }
}

11-practise-hub/package.json (Vite UI)
JSON
{
  "name": "11-practise-hub",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "vite": "^5.0.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  }
}
question-gen/package.json (Batch Logic)
JSON
{
  "name": "question-gen",
  "version": "1.0.0",
  "dependencies": {
    "axios": "^1.6.0"
  },
  "scripts": {
    "start": "node index.js"
  }
}
supabase/package.json (Database Config)
Note: If this folder only contains migrations and config files, you might only need a simple package file to manage Supabase CLI versions.

JSON
{
  "name": "supabase",
  "devDependencies": {
    "supabase": "latest"
  }
}