import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useWorldbookPage } from '../useWorldbookPage';

vi.mock('../../services/modules/worldbook', () => ({
  listWorldbook: vi.fn(),
  getWorldbookEntry: vi.fn(),
  importWorldbook: vi.fn(),
  semanticSearchWorldbook: vi.fn(),
  deleteWorldbookEntry: vi.fn(),
  deleteWorldbookCategory: vi.fn(),
  deleteAllWorldbook: vi.fn(),
}));

describe('useWorldbookPage', () => {
  beforeEach(async () => {
    localStorage.clear();
    vi.resetModules();
    vi.clearAllMocks();

    const api = await import('../../services/modules/worldbook');
    api.listWorldbook.mockResolvedValue({
      items: [
        { worldbook_id: 'Wabc1234', entry_id: 'e1', category: '地理', title: '王城', content: '中心城市', tags: ['城池'], enabled: true, disable: false },
        { worldbook_id: 'Wabc1234', entry_id: 'e2', category: '人物', title: '国王', content: '统治者', tags: ['人物'], enabled: true, disable: false },
        { worldbook_id: 'Wxyz5678', entry_id: 'e3', category: '地理', title: '边境', content: '北方边境', tags: ['地区'], enabled: true, disable: false },
      ],
      total_pages: 1,
    });
    api.getWorldbookEntry.mockImplementation(async (entryId) => ({
      worldbook_id: entryId === 'e3' ? 'Wxyz5678' : 'Wabc1234',
      entry_id: entryId,
      category: entryId === 'e2' ? '人物' : '地理',
      title: entryId === 'e2' ? '国王' : entryId === 'e3' ? '边境' : '王城',
      content: 'detail',
      tags: [],
      canonical: false,
      meta: {},
    }));
  });

  it('shows modules under the selected world only', async () => {
    const page = useWorldbookPage();

    await page.bootstrap();

    expect(page.selectedWorldId.value).toBe('Wabc1234');
    expect(page.selectedWorldModules.value).toHaveLength(2);
    expect(page.selectedWorldModules.value.map((module) => module.name)).toEqual(['地理', '人物']);
  });

  it('supports enabling multiple worldbooks at the same time', async () => {
    const page = useWorldbookPage();

    await page.bootstrap();
    page.toggleSelectedWorldApplied(true);
    await page.applySelection('Wxyz5678');
    page.toggleSelectedWorldApplied(true);

    expect(page.appliedWorldIds.value).toEqual(expect.arrayContaining(['Wabc1234', 'Wxyz5678']));
    expect(page.appliedWorldSummary.value).toContain('Wabc1234');
    expect(page.appliedWorldSummary.value).toContain('Wxyz5678');
  });

  it('keeps entry enabled state in memory when category is turned off', async () => {
    const api = await import('../../services/modules/worldbook');
    api.importWorldbook.mockResolvedValue({ worldbook_id: 'Wabc1234', created: 0, updated: 1 });

    const page = useWorldbookPage();
    await page.bootstrap();

    const geographyModule = page.selectedWorldModules.value.find((module) => module.name === '地理');
    const entry = geographyModule.entries[0];

    await page.toggleEntryEnabled(entry, true);
    page.setCategoryEnabled('地理', false);

    const disabledModule = page.selectedWorldModules.value.find((module) => module.name === '地理');
    expect(disabledModule.enabled).toBe(false);
    expect(disabledModule.entries[0].enabled).toBe(true);
    expect(disabledModule.entries[0].effectiveEnabled).toBe(false);

    page.setCategoryEnabled('地理', true);
    const restoredModule = page.selectedWorldModules.value.find((module) => module.name === '地理');
    expect(restoredModule.entries[0].enabled).toBe(true);
  });

  it('imports legacy category-based worldbook files as standalone worldbooks', async () => {
    const api = await import('../../services/modules/worldbook');
    api.importWorldbook.mockResolvedValue({
      worldbook_id: 'Wnew1234',
      created: 2,
      updated: 0,
    });
    api.listWorldbook.mockResolvedValueOnce({
      items: [
        { worldbook_id: 'Wnew1234', entry_id: 'e10', category: '地理', title: '王城', content: '中心城市', tags: ['城池'], enabled: true, disable: false },
        { worldbook_id: 'Wnew1234', entry_id: 'e11', category: '人物', title: '国王', content: '王国统治者', tags: ['人物'], enabled: true, disable: false },
      ],
      total_pages: 1,
    });

    const page = useWorldbookPage();

    await page.importFiles(
      [
        {
          name: 'legacy.json',
          text: async () =>
            JSON.stringify({
              name: '旧设定集',
              description: '一份旧格式世界书',
              categories: {
                地理: [{ title: '王城', content: '中心城市', tags: ['城池'] }],
                人物: [{ title: '国王', content: '王国统治者', tags: ['人物'] }],
              },
            }),
        },
      ],
      'world',
    );

    expect(api.importWorldbook).toHaveBeenCalledWith(
      {
        entries: [
          expect.objectContaining({ category: '地理', title: '王城' }),
          expect.objectContaining({ category: '人物', title: '国王' }),
        ],
      },
      false,
    );
    expect(page.selectedWorldId.value).toBe('Wnew1234');
    expect(page.metaMap.value.Wnew1234.name).toBe('旧设定集');
  });
});
