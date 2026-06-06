from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from Backend.Extraccion.Extraccion_ERP.Formato_vergel import extraer_libro_auxiliar
from Backend.Extraccion.Extraccion_bancos.Agrario import extraer_extracto_agrario
from Backend.Extraccion.Extraccion_bancos.Nequi import extraer_movimientos_nequi
from Backend.ExportacionExcel.Exportar_resultado_conciliacion import exportar_resultado_conciliacion
from Backend.MotorComparacion.Motor_compuesto import detectar_compuestos
from Backend.MotorComparacion.Motor_conciliacion import conciliar_con_matriz_scoring
from Backend.Normalizacion.Normalizacion_agrario.Normalizacion_extractoAgrario import (
    normalizar_agrario,
    separar_conceptos_banco_agrario,
)
from Backend.Normalizacion.Normalizacion_nequi.Normalizacion_erpNequi import normalizar_erp_nequi
from Backend.Normalizacion.Normalizacion_nequi.Normalizacion_extractoNequi import (
    normalizar_nequi,
    separar_conceptos_banco_nequi,
)


@dataclass(frozen=True)
class ReconciliationResult:
    status: str
    output_path: Path
    output_file: str
    erp_rows: int | None = None
    bank_rows: int | None = None
    reconciled_rows: int | None = None
    compound_rows: int | None = None


def _resolve_output_path(output_path=None):
    if output_path is not None:
        return Path(output_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path.cwd() / f"resultado_conciliacion_{timestamp}.xlsx"


def _validate_bank_type(bank_type):
    if bank_type not in {"nequi", "agrario"}:
        raise ValueError(f"Unsupported bank_type: {bank_type}")


def _extract_bank(bank_pdf_path, bank_pdf_password=None, bank_type="nequi"):
    if bank_type == "nequi":
        return extraer_movimientos_nequi(bank_pdf_path, password=bank_pdf_password)

    if bank_type == "agrario":
        return extraer_extracto_agrario(bank_pdf_path)

    _validate_bank_type(bank_type)


def _normalize_bank(df_bank, bank_type="nequi"):
    if bank_type == "nequi":
        df_bank_normalized = normalizar_nequi(df_bank)
        return separar_conceptos_banco_nequi(df_bank_normalized)

    if bank_type == "agrario":
        df_bank_normalized = normalizar_agrario(df_bank)
        return separar_conceptos_banco_agrario(df_bank_normalized)

    _validate_bank_type(bank_type)


def run_reconciliation(
    erp_pdf_path,
    bank_pdf_path,
    bank_pdf_password=None,
    output_path=None,
    bank_type="nequi",
):
    resolved_output_path = _resolve_output_path(output_path)
    _validate_bank_type(bank_type)

    df_erp = extraer_libro_auxiliar(erp_pdf_path)
    df_bank = _extract_bank(
        bank_pdf_path,
        bank_pdf_password=bank_pdf_password,
        bank_type=bank_type,
    )
    df_erp_normalized = normalizar_erp_nequi(df_erp)
    df_bank_reconcilable, df_bank_concepts = _normalize_bank(
        df_bank,
        bank_type=bank_type,
    )
    df_resultado, _ = conciliar_con_matriz_scoring(
        df_banco=df_bank_reconcilable,
        df_erp=df_erp_normalized,
        devolver_matriz=True,
    )
    df_compuestos = detectar_compuestos(df_resultado)

    exportar_resultado_conciliacion(
        df_resultado,
        df_compuestos,
        nombre_archivo=resolved_output_path,
        df_conceptos_banco=df_bank_concepts,
        df_banco_extraido=df_bank,
        df_libro_auxiliar_extraido=df_erp,
    )

    return ReconciliationResult(
        status="completed",
        output_path=resolved_output_path,
        output_file=resolved_output_path.name,
        erp_rows=len(df_erp_normalized),
        bank_rows=len(df_bank_reconcilable),
        reconciled_rows=len(df_resultado),
        compound_rows=len(df_compuestos),
    )
