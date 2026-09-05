import React from "react";

export default class EngineErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("NETRAAI ENGINE CRASH:", error);
    console.error(info);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            minHeight: "70vh",
            margin: "30px",
            padding: "32px",
            background: "#07131b",
            border: "1px solid #ff6e78",
            color: "#eef7fb",
            fontFamily: "monospace",
          }}
        >
          <h2 style={{ color: "#ff8d96" }}>
            NetraAI Engine Runtime Error
          </h2>

          <p>
            The screening page crashed while rendering.
          </p>

          <pre
            style={{
              whiteSpace: "pre-wrap",
              color: "#ffd6d9",
              lineHeight: 1.6,
            }}
          >
            {String(this.state.error?.stack || this.state.error)}
          </pre>
        </div>
      );
    }

    return this.props.children;
  }
}
