import { useEffect, useState } from "react";

export default function LaunchScreen({ onComplete }) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const hold = setTimeout(() => {
      setLeaving(true);

      const exit = setTimeout(() => {
        onComplete?.();
      }, 500);

      return () => clearTimeout(exit);
    }, 1400);

    return () => clearTimeout(hold);
  }, [onComplete]);

  return (
    <div className={`netra-launch-simple ${leaving ? "leaving" : ""}`}>
      <img
        src="/netraai-logo.png"
        alt="NetraAI"
        className="netra-launch-simple-logo"
      />
    </div>
  );
}
