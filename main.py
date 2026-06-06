import argparse

from Backend.Servicios.conciliacion_service import run_reconciliation


def build_parser():
    parser = argparse.ArgumentParser(description="Run local bank reconciliation")
    parser.add_argument("--erp-pdf", required=True)
    parser.add_argument("--bank-pdf", required=True)
    parser.add_argument("--bank-pdf-password")
    parser.add_argument("--output")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    result = run_reconciliation(
        args.erp_pdf,
        args.bank_pdf,
        bank_pdf_password=args.bank_pdf_password,
        output_path=args.output,
    )
    print(f"Reconciliation completed: {result.output_path}")
    return result


if __name__ == "__main__":
    main()
