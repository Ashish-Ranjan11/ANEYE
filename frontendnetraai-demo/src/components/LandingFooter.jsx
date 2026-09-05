import { Link } from "react-router-dom";

export default function LandingFooter() {
  return (
    <footer className="footer-final">

      <div className="footer-final-inner">

        <div className="footer-final-brand">

          <div className="footer-logo-plate">
            <img
              src="/netraai-logo.png"
              alt="NetraAI"
            />
          </div>

          <p>
            Explainable diabetic-retinopathy screening
            built around global severity prediction,
            local pathology evidence and reliability-aware
            referral.
          </p>

          <span>
            SIH26038 · TEAM TECHSTERS
          </span>

        </div>


        <div className="footer-final-nav">

          <div>
            <span>PRODUCT</span>

            <Link to="/engine">
              Screening Engine
            </Link>

            <Link to="/engine?demo=grade0">
              Grade 0 Demo
            </Link>

            <Link to="/engine?demo=grade1">
              Grade 1 Demo
            </Link>

            <Link to="/engine?demo=grade2">
              Grade 2 Demo
            </Link>
          </div>


          <div>
            <span>PIPELINE</span>

            <p>Image Quality Gate</p>
            <p>ICDR Grade 0–4</p>
            <p>Referable DR</p>
            <p>Lesion Segmentation</p>
            <p>Grad-CAM</p>
            <p>TRACE-DR</p>
          </div>


          <div>
            <span>RESPONSIBLE AI</span>

            <p>
              Screening support,
              not autonomous diagnosis.
            </p>

            <p>
              Uncertain cases are routed
              for human review.
            </p>

            <p>
              Prototype P-Score and T-Score
              are system indices.
            </p>
          </div>

        </div>

      </div>


      <div className="footer-final-bottom">

        <span>
          © 2026 NETRAAI
        </span>

        <span>
          EXPLAINABLE RETINAL INTELLIGENCE
        </span>

        <span>
          HUMAN-IN-THE-LOOP
        </span>

      </div>

    </footer>
  );
}
