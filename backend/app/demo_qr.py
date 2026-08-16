from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from urllib.parse import urlsplit

import qrcode
from qrcode.image.svg import SvgPathFillImage

from app.config import load_settings
from app.deployment import DeploymentPreflightResult, validate_production_deployment


@dataclass(frozen=True, slots=True)
class QRArtifactResult:
    output: str
    public_api_base_url: str
    frontend_base_url: str
    qr_entry_url: str


def generate_qr_svg(entry_url: str, output: Path, *, force: bool = False) -> Path:
    """HTTPS 진입 URL을 인쇄 가능한 흰 배경 SVG QR로 생성한다."""
    # [Backend-07-'시연 QR SVG 생성'] 고객 식별자 없이 opaque 진입 토큰 URL만 QR에 인코딩한다.
    parsed = urlsplit(entry_url)
    token = parsed.path.removeprefix("/entry/")
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/entry/")
        or "/" in token
        or len(token) < 24
    ):
        raise ValueError("QR에는 검증된 HTTPS /entry/{token} URL만 사용할 수 있습니다.")
    if output.suffix.lower() != ".svg":
        raise ValueError("QR 출력 파일 확장자는 .svg여야 합니다.")
    if output.exists() and not force:
        raise FileExistsError("QR 파일이 이미 존재합니다. 덮어쓰려면 --force를 사용하세요.")

    output.parent.mkdir(parents=True, exist_ok=True)
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
        image_factory=SvgPathFillImage,
    )
    qr.add_data(entry_url)
    qr.make(fit=True)
    qr.make_image().save(output)
    return output.resolve()


def _safe_result(preflight: DeploymentPreflightResult, output: Path) -> QRArtifactResult:
    hidden_preflight = replace(
        preflight,
        qr_entry_url=f"{preflight.public_api_base_url}/entry/<hidden>",
    )
    return QRArtifactResult(
        output=str(output),
        public_api_base_url=hidden_preflight.public_api_base_url,
        frontend_base_url=hidden_preflight.frontend_base_url,
        qr_entry_url=hidden_preflight.qr_entry_url,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="M-Journey 시연용 인쇄 QR SVG 생성")
    parser.add_argument("--output", type=Path, required=True, help="생성할 .svg 파일 경로")
    parser.add_argument("--force", action="store_true", help="기존 SVG 파일 덮어쓰기")
    args = parser.parse_args()

    settings = load_settings()
    preflight = validate_production_deployment(
        settings,
        public_api_base_url=os.getenv("M_JOURNEY_PUBLIC_API_BASE_URL"),
        jwt_secret=os.getenv("M_JOURNEY_JWT_SECRET"),
        demo_password=os.getenv("M_JOURNEY_DEMO_PASSWORD"),
        demo_qr_token=os.getenv("M_JOURNEY_DEMO_QR_TOKEN"),
        show_qr_url=True,
    )
    output = generate_qr_svg(preflight.qr_entry_url, args.output, force=args.force)
    print(json.dumps(asdict(_safe_result(preflight, output)), ensure_ascii=False))


if __name__ == "__main__":
    main()
