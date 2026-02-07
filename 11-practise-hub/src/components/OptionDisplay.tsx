import { MathText } from '@/components/MathText';

interface OptionDisplayProps {
  option_text: string;
  option_image_url?: string;
  size?: 'small' | 'medium' | 'large';
}

/** Renders an answer option as image and/or text (for picture-based and text-only questions). */
export function OptionDisplay({
  option_text,
  option_image_url,
  size = 'medium',
}: OptionDisplayProps) {
  const imgClass =
    size === 'small'
      ? 'max-h-16 min-h-12 w-auto object-contain'
      : size === 'large'
        ? 'max-h-44 min-h-32 w-auto object-contain'
        : 'max-h-28 min-h-20 w-auto object-contain';
  return (
    <span className="inline-flex items-center gap-3">
      {option_image_url ? (
        <img
          src={option_image_url}
          alt=""
          className={imgClass}
          referrerPolicy="no-referrer"
          data-option-image-url={option_image_url}
          onError={(e) => {
            e.currentTarget.style.display = 'none';
            console.error('Option image failed to load:', option_image_url);
          }}
        />
      ) : null}
      {option_text ? (
        <MathText component="span">{option_text}</MathText>
      ) : null}
    </span>
  );
}
