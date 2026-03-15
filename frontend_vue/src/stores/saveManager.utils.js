export const DEV_MODE_KEY = 'storyteller_developer_mode_v1';

export function loadDeveloperMode() {
  try {
    return window.localStorage.getItem(DEV_MODE_KEY) === '1';
  } catch {
    return false;
  }
}

export function fallbackName(sessionId) {
  return sessionId || '未载入存档';
}

export function normalizeSave(item = {}) {
  return {
    session_id: item.session_id || '',
    display_name: item.display_name || item.branch_display_name || item.session_id || '',
    updated_at: item.updated_at || null,
    created_at: item.created_at || null,
    segment_count: item.segment_count ?? 0,
    total_word_count: item.total_word_count ?? 0,
    story_id: item.story_id || `session:${item.session_id || 'unknown'}`,
    story_title: item.story_title || item.display_name || item.session_id || '未命名故事',
    branch_id: item.branch_id || null,
    branch_display_name: item.branch_display_name || item.display_name || item.session_id || '未命名会话',
    branch_type: item.branch_type || null,
    branch_status: item.branch_status || null,
    parent_branch_id: item.parent_branch_id || null,
    reasoning_strength: item.reasoning_strength || null,
  };
}

export function buildStoryTree(items = []) {
  const stories = new Map();
  for (const raw of items) {
    const item = normalizeSave(raw);
    if (!stories.has(item.story_id)) {
      stories.set(item.story_id, {
        story_id: item.story_id,
        story_title: item.story_title,
        updated_at: item.updated_at,
        total_word_count: 0,
        session_count: 0,
        sessions: [],
      });
    }
    const story = stories.get(item.story_id);
    story.story_title = item.story_title || story.story_title;
    story.updated_at = [story.updated_at, item.updated_at].filter(Boolean).sort().reverse()[0] || story.updated_at;
    story.total_word_count += item.total_word_count || 0;
    story.session_count += 1;
    story.sessions.push(item);
  }
  return [...stories.values()]
    .map((story) => ({
      ...story,
      sessions: story.sessions.sort((a, b) => `${b.updated_at || ''}`.localeCompare(`${a.updated_at || ''}`)),
    }))
    .sort((a, b) => `${b.updated_at || ''}`.localeCompare(`${a.updated_at || ''}`));
}

export function pickSessionId(story, preferredId = '') {
  if (!story?.sessions?.length) return '';
  if (preferredId && story.sessions.some((item) => item.session_id === preferredId)) {
    return preferredId;
  }
  return story.sessions[0]?.session_id || '';
}
