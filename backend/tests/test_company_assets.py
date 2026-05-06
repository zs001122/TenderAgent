from sqlmodel import SQLModel, Session, create_engine

from app.db.repository import CompanyRepository


def make_repo():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    return CompanyRepository(session), session


def test_company_asset_manual_crud_and_soft_delete():
    repo, session = make_repo()
    try:
        created = repo.create_asset({
            "asset_type": "qualification",
            "source_sheet": "手工维护",
            "name": "测试资质",
            "status": "有效",
            "keywords": ["测试", "资质"],
            "data": {"备注": "人工新增"},
        })

        assert created["id"] is not None
        assert created["source_type"] == "manual"
        assert repo.count_assets() == 1

        updated = repo.update_asset(created["id"], {
            "asset_type": "qualification",
            "source_sheet": "手工维护",
            "name": "测试资质-已更新",
            "status": "有效",
            "keywords": ["更新"],
            "data": {"备注": "人工编辑"},
        })

        assert updated["name"] == "测试资质-已更新"
        assert updated["source_type"] == "manual"
        assert updated["keywords"] == ["更新"]

        deleted = repo.soft_delete_asset(created["id"], "误录入")
        assert deleted["is_deleted"] is True
        assert deleted["deleted_reason"] == "误录入"
        assert repo.count_assets() == 0
        assert repo.count_assets(include_deleted=True) == 1
        assert repo.get_assets() == []
        assert len(repo.get_assets(include_deleted=True)) == 1

        restored = repo.restore_asset(created["id"])
        assert restored["is_deleted"] is False
        assert repo.count_assets() == 1
    finally:
        session.close()
