import { Component, ReactNode } from "react";
import type { ErrorInfo } from "react";
import { getErrorMessageSafe } from "./api";

export function formatSafeErrorSummary(error: unknown): string {
  const message = getErrorMessageSafe(error);
  return redactBoundaryErrorText(message || "A local UI panel failed to render.");
}

function redactBoundaryErrorText(value: string): string {
  return value
    .replace(/\n\s*at\s+[\s\S]*/g, "\n[stack trace redacted]")
    .replace(/stack\s*[:=]\s*[\s\S]*/gi, "stack=[redacted]")
    .replace(/Traceback[\s\S]*/gi, "[stack trace redacted]")
    .replace(/sk-[A-Za-z0-9_-]+/g, "sk-[redacted]")
    .replace(/(authorization\s*[:=]\s*)(bearer\s+)?[A-Za-z0-9._~+/=-]+/gi, "[redacted authorization]")
    .replace(/((?:transient[_-]?)?api[_-]?key|secret[_-]?ref|provider[_-]?secret|relay[_-]?token|access[_-]?token|secret|token|password)\s*[:=]\s*['"]?[^'",\s}\]]+/gi, "$1=[redacted]")
    .replace(/([?&](?:api[_-]?key|key|token|access[_-]?token|secret|signature|sig|auth|authorization)=)[^&#\s"'<>]+/gi, "$1[redacted]")
    .replace(/(\/(?:token|tokens|key|keys|secret|secrets|bearer|auth)\/)[A-Za-z0-9._~+/=-]{8,}/gi, "$1[redacted]")
    .replace(/[A-Z]:\\[^\s"'<>]+/g, "[local path redacted]")
    .replace(/\/[^\s"'<>]*(?:\.env|\.db|\.sqlite|logs?|cache|backups?|crash-reports|node_modules|dist)[^\s"'<>]*/gi, "[local path redacted]")
    .replace(/(hidden[_\s-]?facts?|npc[_\s-]?secrets?|npc[_\s-]?knowledge|raw[_\s-]?prompts?|raw[_\s-]?env|state[_\s-]?deltas?|debug[_\s-]?memory|private[_\s-]?notes?)\s*[:=]\s*[^}\n]+/gi, "$1=[redacted]")
    .trim();
}

type AppErrorBoundaryProps = {
  label: string;
  children: ReactNode;
  onGoHome?: () => void;
  resetKey?: string | number | boolean | null;
};

type AppErrorBoundaryState = {
  hasError: boolean;
  safeSummary: string;
};

export class AppErrorBoundary extends Component<AppErrorBoundaryProps, AppErrorBoundaryState> {
  private titleRef: HTMLHeadingElement | null = null;

  constructor(props: AppErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, safeSummary: "" };
  }

  static getDerivedStateFromError(error: unknown): AppErrorBoundaryState {
    return {
      hasError: true,
      safeSummary: formatSafeErrorSummary(error)
    };
  }

  componentDidCatch(_error: Error, _errorInfo: ErrorInfo) {
    // Normal UI deliberately avoids stack traces and raw component payloads.
  }

  componentDidUpdate(previousProps: AppErrorBoundaryProps, previousState: AppErrorBoundaryState) {
    if (previousProps.resetKey !== this.props.resetKey && this.state.hasError) {
      this.setState({ hasError: false, safeSummary: "" });
      return;
    }
    if (!previousState.hasError && this.state.hasError) {
      window.setTimeout(() => {
        try {
          this.titleRef?.focus({ preventScroll: false });
        } catch {
          this.titleRef?.focus();
        }
      }, 0);
    }
  }

  private retry = () => {
    this.setState({ hasError: false, safeSummary: "" });
  };

  private goHome = () => {
    if (this.props.onGoHome) {
      this.props.onGoHome();
      this.retry();
      return;
    }
    window.location.assign(window.location.pathname || "/");
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <section
        className="route-error-state app-error-boundary"
        role="alert"
        aria-live="assertive"
        data-v36-error-boundary="safe"
      >
        <p className="eyebrow">Local UI Error Boundary</p>
        <h2 ref={(node) => { this.titleRef = node; }} tabIndex={-1}>
          {this.props.label} could not render
        </h2>
        <p>{this.state.safeSummary || "A local UI panel failed to render."}</p>
        <div className="button-row">
          <button type="button" onClick={this.retry}>
            Retry local panel
          </button>
          <button type="button" onClick={this.goHome}>
            Go Home
          </button>
        </div>
        <p className="muted">
          Diagnostics remain local-only. Use Diagnostics Bundle Review to preview a redacted report; no stack trace, API key, raw env, hidden facts, or sensitive local path is shown here.
        </p>
      </section>
    );
  }
}
