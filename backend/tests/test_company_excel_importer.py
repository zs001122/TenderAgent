from pathlib import Path

from app.services.company_excel_importer import CompanyExcelImporter


def test_import_current_company_workbook():
    workbook = next(Path(__file__).resolve().parents[2].glob("*.xlsx"))

    result = CompanyExcelImporter().parse(workbook.read_bytes())

    assert result["company_name"] == "广州智算信息技术有限公司"
    assert result["summary"]["total_assets"] > 0
    assert result["summary"]["by_sheet"]["专业资质认证"] > 0
    assert result["summary"]["by_sheet"]["人员"] > 0
    assert result["summary"]["by_sheet"]["业绩"] > 0
    assert any(asset["name"] for asset in result["assets"] if asset["asset_type"] == "qualification")
