import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useCharactersPage } from '../useCharactersPage';

vi.mock('../../services/modules/characters', () => ({
  listCharacters: vi.fn(),
  getCharacter: vi.fn(),
  importCharacters: vi.fn(),
  updateCharacter: vi.fn(),
  deleteCharacter: vi.fn(),
  clearAllCharacters: vi.fn(),
  exportAllCharacters: vi.fn(),
}));

vi.mock('../../services/modules/templates', () => ({
  listTemplates: vi.fn(),
  createTemplate: vi.fn(),
  updateTemplate: vi.fn(),
  deleteTemplate: vi.fn(),
}));

vi.mock('../../services/modules/story', () => ({
  updateSessionContext: vi.fn(),
}));

vi.mock('../../stores/session', () => ({
  useSessionStore: () => ({
    bootstrap: vi.fn(),
    currentSessionId: 'SAVE_001',
  }),
}));

describe('useCharactersPage', () => {
  beforeEach(async () => {
    vi.resetModules();
    vi.clearAllMocks();

    const charactersApi = await import('../../services/modules/characters');
    const templatesApi = await import('../../services/modules/templates');

    templatesApi.listTemplates.mockResolvedValue({ items: [] });
    charactersApi.listCharacters.mockResolvedValue({
      items: [{ character_id: 'NPC_001', basic: { name: '林秋' }, type: 'npc' }],
    });
    charactersApi.getCharacter.mockResolvedValue({
      character_id: 'NPC_001',
      type: 'npc',
      template_id: 'system_default',
      tab_basic: { name: '林秋', profile: '旧简介' },
      tab_knowledge: {},
      tab_attributes: {},
      tab_relations: {},
      tab_items: [],
    });
    charactersApi.updateCharacter.mockResolvedValue({});
  });

  it('saves edited character detail', async () => {
    const charactersApi = await import('../../services/modules/characters');
    const page = useCharactersPage();

    await page.bootstrap();
    page.updateField({ id: 'f_profile', path: 'tab_basic.profile', type: 'textarea' }, '新简介');
    await page.saveCharacter();

    expect(charactersApi.updateCharacter).toHaveBeenCalledWith(
      'NPC_001',
      expect.objectContaining({
        character_id: 'NPC_001',
        tab_basic: expect.objectContaining({
          name: '林秋',
          profile: '新简介',
        }),
      }),
    );
  });
});
