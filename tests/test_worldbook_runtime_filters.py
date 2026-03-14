import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core import orchestrator
from backend.db.base import Base
from backend.db import models


def _create_user(db, user_id: str, username: str):
    user = models.User(
        user_id=user_id,
        username=username,
        password_hash='hashed',
        role=models.UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def test_worldbook_snippets_only_use_active_worldbook_and_enabled_categories():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        user = _create_user(db, 'u_world_runtime', 'runtime_user')
        db.add(models.GlobalSetting(
            user_id=user.user_id,
            key=f'global::{user.user_id}',
            value_json=json.dumps({
                'worldbook': {
                    'active_worldbook_id': 'Wactive1',
                    'category_switches': {
                        'Wactive1::location': False,
                    },
                },
            }, ensure_ascii=False),
        ))
        db.add_all([
            models.WorldbookEntry(
                user_id=user.user_id,
                worldbook_id='Wactive1',
                entry_id='e_active_allowed',
                category='character',
                title='klein',
                content='nighthawk member',
                importance=0.9,
                meta_json=json.dumps({'enabled': True, 'disable': False}, ensure_ascii=False),
            ),
            models.WorldbookEntry(
                user_id=user.user_id,
                worldbook_id='Wactive1',
                entry_id='e_active_blocked_category',
                category='location',
                title='tingen',
                content='disabled category content',
                importance=1.0,
                meta_json=json.dumps({'enabled': True, 'disable': False}, ensure_ascii=False),
            ),
            models.WorldbookEntry(
                user_id=user.user_id,
                worldbook_id='Wother01',
                entry_id='e_other_world',
                category='character',
                title='suyao',
                content='other worldbook content',
                importance=1.0,
                meta_json=json.dumps({'enabled': True, 'disable': False}, ensure_ascii=False),
            ),
            models.WorldbookEntry(
                user_id=user.user_id,
                worldbook_id='Wactive1',
                entry_id='e_disabled_entry',
                category='character',
                title='disabled-entry',
                content='should not inject',
                importance=1.0,
                meta_json=json.dumps({'enabled': False, 'disable': True}, ensure_ascii=False),
            ),
        ])
        db.commit()

        active_worldbook_id, category_switches = orchestrator._load_worldbook_runtime_state(db, user.user_id)
        snippets = orchestrator._worldbook_snippets(
            db,
            user_id=user.user_id,
            context_text=None,
            limit=10,
            active_worldbook_id=active_worldbook_id,
            category_switches=category_switches,
        )

        entry_ids = {item['entry_id'] for item in snippets}
        assert entry_ids == {'e_active_allowed'}
    finally:
        db.close()
