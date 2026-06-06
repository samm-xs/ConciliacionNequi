from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

from Backend.Servicios.conciliacion_service import run_reconciliation


FRONTEND_HTML_PATH = Path(__file__).resolve().parents[2] / "Frontend" / "Diseño_mvp.html"


def create_app(output_dir=None, reconciliation_runner=run_reconciliation):
    app = FastAPI(title="Local Reconciliation API")
    resolved_output_dir = Path(output_dir) if output_dir is not None else Path.cwd() / "outputs"
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    @app.get("/")
    def frontend():
        return FileResponse(FRONTEND_HTML_PATH)

    @app.post("/api/reconciliations")
    async def create_reconciliation(
        erp_pdf: UploadFile = File(...),
        bank_pdf: UploadFile = File(...),
        bank_pdf_password: str | None = Form(None),
        password_banco: str | None = Form(None),
        bank_type: str = Form("nequi"),
    ):
        with TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            erp_path = temp_dir_path / erp_pdf.filename
            bank_path = temp_dir_path / bank_pdf.filename
            erp_path.write_bytes(await erp_pdf.read())
            bank_path.write_bytes(await bank_pdf.read())
            output_path = resolved_output_dir / "resultado.xlsx"
            password = bank_pdf_password if bank_pdf_password is not None else password_banco

            try:
                result = reconciliation_runner(
                    erp_path,
                    bank_path,
                    bank_pdf_password=password,
                    output_path=output_path,
                    bank_type=bank_type,
                )
            except Exception as exc:
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "detail": str(exc)},
                )

        response = {
            "status": result.status,
            "output_file": result.output_file,
            "output_path": str(result.output_path),
            "download_url": f"/api/reconciliations/{result.output_file}/download",
            "erp_rows": result.erp_rows,
            "bank_rows": result.bank_rows,
            "reconciled_rows": result.reconciled_rows,
            "compound_rows": result.compound_rows,
        }
        return response

    @app.get("/api/reconciliations/{filename}/download")
    def download_reconciliation(filename: str):
        file_path = (resolved_output_dir / filename).resolve()

        if resolved_output_dir.resolve() not in file_path.parents or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(file_path)

    return app


app = create_app()
