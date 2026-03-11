(function () {
  // =========================================================
  // 0. 闂傚倸鍊搁崐宄懊归崶褏鏆﹂柛顭戝亝閸欏繘鏌熼幆鏉啃撻柍閿嬫⒒閳ь剙绠嶉崕閬嵥囬婊冾棜閻熸瑥瀚粻楣冩煙鐎涙鎳冮柣蹇ｄ邯閺屾稒鎯旈埥鍛紣濡炪値鍙€濞夋洟骞戦崟顖涘€绘俊顖滅帛鐎氭娊姊虹拠鎻掝劉缁炬澘绉撮悾婵堢矙濞嗙偓缍庡┑鐐叉▕娴滄粓宕归崒娑栦簻闁哄洨鍋為崳褰掓煕閹惧啿鏆遍柍瑙勫灴閹晠顢曢～顓烆棜闂傚倷绀佸﹢閬嶆惞鎼淬劌绐楅柡宥庡亞濡垳鎲搁弮鍫濊摕婵炴垯鍩勯弫鍐煥濠靛棙宸濋柣锝嗘そ濮婃椽妫冮埡鍐╁仹闂佺娅曢幑鍥春閻愬搫绠ｉ柨鏃傜帛閺咁亪姊洪崨濠佺繁闁告挾鍠栧畷鎴澪旈崨顔尖偓鐢告偡濞嗗繐顏紒鈧崘顔界厽闁绘柨寮跺▍濠冾殽閻愯韬柟顔界懇瀹曨偊宕熸惔娑樺闁哄被鍔戝顕€宕掑鍕晵闂備礁鎽滈崯鍧楀磻?
  // =========================================================
  function getAuthToken() {
    return typeof Auth !== 'undefined' ? Auth.getToken() : localStorage.getItem('auth_token');
  }

  function authFetch(url, options = {}) {
    const token = getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return fetch(url, { ...options, headers });
  }

  // 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠煑閼恒儳鈽夐柍璇查叄楠炴ê鐣烽崶璺烘暪闂傚倷绀侀幉锟犲礉濮椻偓椤㈡艾顭ㄩ崼鐔锋畬闂佺鍕垫畷闁绘挻娲橀妵鍕箛閸撲胶蓱缂備讲鍋撻柍褜鍓涚槐鎾存媴閹绘帊澹曢梻浣虹《閸撴繄绮欓幒妤佸亗婵炴垶锕╅悢鍡涙偣閾忕懓鐨戦柛鏃傚枎闇夐柣姗嗗枛閻忣噣鏌嶈閸撴岸顢欓弽顓炵獥闁哄诞宀€鍔烽梺璺ㄥ枔婵绮婚弽銊﹀弿婵＄偠顕ф禍楣冩⒑鐠団€虫灍闁荤啿鏅犲畷娲焺閸愨晛顎撻悗鐟板閸嬪﹤螞濠婂啠鏀介柣妯虹仛閺嗏晠鏌涚€ｎ剙鈻堟鐐存崌椤㈡棃宕卞Δ鍐摌闂備礁鎲￠幐鍡涘礃閵娧傚枈闂備胶鎳撻崥瀣偩椤忓牆绀夌€光偓閸曨偄鍤戞繛鎾村焹閸嬫捇鏌＄仦鐐鐎规洜鍘ч埞鎴﹀箛椤撳绠撳娲传閸曨偒浠撮梺绋挎捣閺佽顕ｆ繝姘櫜濠㈣泛锕ゅ畵鍡涙⒑缂佹ê濮堢紒浣规尦瀹曟垿骞樼紒妯烘闂侀潧鐗嗗ú銊╂倿閸忚偐绡€闁靛骏绲剧涵鐐亜椤撶偟澧﹂柛鈹惧亾濡炪倖甯婄粈浣虹箔閹烘挶浜滄い鎰剁悼缁犵偞銇勯姀鈽呰€块柟顔规櫊椤㈡洟鏁愭惔銏㈢Ь闂傚倸鍊搁崐椋庣矆娓氣偓楠炲鏁撻悩鍐蹭画閻熸粍鏌ㄩ悾鐑藉箣閿曗偓缁犲鏌涢幘鑼跺厡闁绘帒娼″娲捶椤撶偛濡哄銈冨妼閹虫ê鐣峰鈧崺鈧い鎺嗗亾妞ゎ亜鍟存俊鑸垫償閳ュ磭顔愬┑鐘绘涧閸婄懓顫忕拠娴嬫瀻闁靛繒濯鈺傘亜閹烘垵鈧懓鈻撻崜褏纾藉ù锝呭閸庢劖銇勯幋鐐垫噧闁靛棙甯楃换婵嗩潩椤撶姴骞嶆俊鐐€栭悧鏇炍涘畝鍕；闁瑰墽绮悡娑㈡倵閿濆簼绨界紒鐘电帛閹?
  window.getAuthToken = getAuthToken;
  window.authFetch = authFetch;

  // --- UI 闂傚倸鍊搁崐鎼佸磹閻戣姤鍤勯柛顐ｆ磵閳ь剨绠撳畷濂稿閳ュ啿绨ラ梻浣告贡婢ф顭垮鈧幃鍧楊敋閳ь剟寮婚悢灏佹灁闁割煈鍠楅悘鎾绘⒑濞茶骞栨俊顐ｇ箞楠炲啫顫滈埀顒勫箖濞嗘挻鍋ㄩ柛顭戝亝閸熸帡姊绘担瑙勫仩闁稿﹥鐗曠叅闁绘梻鍘ч拑鐔兼煥閻斿搫孝闁绘劕锕弻宥嗘姜閹殿喗鍋ч梺鎸庣箓椤︿即鎮?---
  // Tabs
  const tabButtons = document.querySelectorAll('.settings-tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  // Visual Selectors
  const themeOptions = document.querySelectorAll('#theme-grid .visual-option');
  const bgOptions = document.querySelectorAll('#bg-grid .visual-option');

  // Form Fields
  const postprocessingRulesEl = document.getElementById("postprocessing-rules");
  const summaryEnabledEl = document.getElementById("summary-enabled");
  const summaryProfileIdEl = document.getElementById("summary-profile-id");
  const summaryFrequencyEl = document.getElementById("summary-frequency");
  const summaryRagConfigEl = document.getElementById("summary-rag-config");
  const variablesEnabledEl = document.getElementById("variables-enabled");
  const variablesProfileIdEl = document.getElementById("variables-profile-id");
  const variablesApiConfigIdEl = document.getElementById("variables-api-config-id");
  const alignmentStrictEl = document.getElementById("alignment-strict");
  const alignmentRuleIdEl = document.getElementById("alignment-rule-id");
  const textoptEnabledEl = document.getElementById("textopt-enabled");
  const textoptProfileIdEl = document.getElementById("textopt-profile-id");
  const worldEvolutionEnabledEl = document.getElementById("world-evolution-enabled");
  const worldEvolutionProfileIdEl = document.getElementById("world-evolution-profile-id");
  const defaultProfilesEl = document.getElementById("default-profiles");

  // Typography Fields
  const fontUiFamilyEl = document.getElementById("font-ui-family");
  const fontUiSizeEl = document.getElementById("font-ui-size");
  const fontStoryFamilyEl = document.getElementById("font-story-family");
  const fontStorySizeEl = document.getElementById("font-story-size");
  const fontConsoleFamilyEl = document.getElementById("font-console-family");
  const fontConsoleSizeEl = document.getElementById("font-console-size");
  const fontCharFamilyEl = document.getElementById("font-char-family");
  const fontCharSizeEl = document.getElementById("font-char-size");
  const fontWorldFamilyEl = document.getElementById("font-world-family");
  const fontWorldSizeEl = document.getElementById("font-world-size");
  const fontDungeonFamilyEl = document.getElementById("font-dungeon-family");
  const fontDungeonSizeEl = document.getElementById("font-dungeon-size");

  const DEFAULT_FONT_SIZE = "14px";

  // 闂傚倸鍊搁崐宄懊归崶顒夋晪鐟滃繘鍩€椤掍胶鈻撻柡鍛箘閸掓帒鈻庨幘宕囶唺濠德板€愰崑鎾愁浖閸涘瓨鈷戠紓浣姑慨澶愭煛娴ｅ憡鎲哥紒顔肩墛缁绘繈宕堕妸銉㈠亾閻㈠憡鐓ユ繝闈涙椤庢鏌＄€ｎ偆銆掔紒杈ㄥ浮閸┾偓妞ゆ帒瀚獮銏＄箾閹寸偟鎳呴柛姗€浜跺娲棘閵夛附鐝旈梺鍝ュУ閼归箖鍩㈤幘璇茬睄闁割偆鍟块幏濠氭⒑閸涘﹣绶遍柛锝庡灦閹虫捇骞愭惔銏犲伎婵犵數濮撮崯顖炲Φ濠靛牃鍋撳▓鍨灈濠⒀冮叄楠炴垿宕熼姣尖晠鏌熼幍铏珔闁逞屽墯缁诲牆顕?
  const FONT_ZONES = {
    ui: {
      familyVar: "--font-ui-family",
      sizeVar: "--font-ui-size",
      familyEl: fontUiFamilyEl,
      sizeEl: fontUiSizeEl,
      storageFamilyKey: "app_font_ui_family",
      storageSizeKey: "app_font_ui_size"
    },
    story: {
      familyVar: "--font-story-family",
      sizeVar: "--font-story-size",
      familyEl: fontStoryFamilyEl,
      sizeEl: fontStorySizeEl,
      storageFamilyKey: "app_font_story_family",
      storageSizeKey: "app_font_story_size"
    },
    console: {
      familyVar: "--font-console-family",
      sizeVar: "--font-console-size",
      familyEl: fontConsoleFamilyEl,
      sizeEl: fontConsoleSizeEl,
      storageFamilyKey: "app_font_console_family",
      storageSizeKey: "app_font_console_size"
    },
    character: {
      familyVar: "--font-char-family",
      sizeVar: "--font-char-size",
      familyEl: fontCharFamilyEl,
      sizeEl: fontCharSizeEl,
      storageFamilyKey: "app_font_char_family",
      storageSizeKey: "app_font_char_size"
    },
    world: {
      familyVar: "--font-world-family",
      sizeVar: "--font-world-size",
      familyEl: fontWorldFamilyEl,
      sizeEl: fontWorldSizeEl,
      storageFamilyKey: "app_font_world_family",
      storageSizeKey: "app_font_world_size"
    },
    dungeon: {
      familyVar: "--font-dungeon-family",
      sizeVar: "--font-dungeon-size",
      familyEl: fontDungeonFamilyEl,
      sizeEl: fontDungeonSizeEl,
      storageFamilyKey: "app_font_dungeon_family",
      storageSizeKey: "app_font_dungeon_size"
    }
  };


  // Actions
  const loadBtn = document.getElementById("settings-load-btn");
  const saveBtn = document.getElementById("settings-save-btn");
  const statusEl = document.getElementById("settings-status");

  // State
  let currentSettings = {};
  const GLOBAL_TAB_KEY_MAP = {
    "tab-ui": ["ui", "text"],
    "tab-memory": ["summary"],
    "tab-variables": ["variables"],
    "tab-evolution": ["text_opt", "world_evolution", "default_profiles"]
  };

  function cloneValue(value) {
    if (value == null) return value;
    return JSON.parse(JSON.stringify(value));
  }

  function getActiveTabId() {
    const activeBtn = document.querySelector('.settings-tab-btn.active');
    return activeBtn ? activeBtn.dataset.target : "tab-ui";
  }

  function mergeSettingsByKeys(baseSettings, nextSettings, keys) {
    const merged = cloneValue(baseSettings) || {};
    keys.forEach(key => {
      merged[key] = cloneValue(nextSettings[key]) || {};
    });
    return merged;
  }
  // --- 1. 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠Χ閸モ晝鍘犻梻浣稿閸嬪懎煤瀹ュ鐒垫い鎺戯功閻ｇ數鈧娲栭妶鍛婃叏閳ь剟鏌曡箛瀣仼妞わ腹鏅涢埞鎴炲箠闁稿ě鍛筏濞寸姴顑呴悿顔姐亜閺嶎偄浠﹂柛濠傜仢閳规垿鎮╁畷鍥舵殹闂佺粯鎸婚惄顖炲蓟濞戙垹鍗抽柕濞垮劙缁ㄧ晫绱撴担鍝勑ｅ┑鐐诧躬楠炲啯绂掔€ｅ灚鏅┑顔斤供閸欏骸螞閿曞倹鈷戦柛婵嗗椤箓鏌涢弬璺ㄧ劯闁糕斂鍎插鍕箾閻愵剛鈧姊洪崷顓炲妺闁糕晛鐗嗚灋闁绘棁娅ｇ壕浠嬫煕鐏炲墽鎳囨俊鍓у厴閺屾盯寮捄銊愌囨煙椤曞棛绡€闁轰焦鎹囬幃鈺呮嚑椤掑倹姣囨繝鐢靛仜椤曨厽鎱ㄩ幘顕呮晞闁告侗鍠栭崝鏃堟⒒閸屾瑧绐旀繛浣冲洦鍋嬮柛鈩冪☉缁犵娀鏌熼柇锕€鍔﹂柨婵嗩槹閺呮煡鏌涢埄鍐╃缂?---
  function applyVisuals(theme, bg) {
    if (theme) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('app_theme', theme);
      themeOptions.forEach(opt => {
        if (opt.dataset.value === theme) opt.classList.add('selected');
        else opt.classList.remove('selected');
      });
    }

    if (bg) {
      document.body.classList.forEach(cls => {
        if (cls.startsWith('bg-')) document.body.classList.remove(cls);
      });
      document.body.classList.add(`bg-${bg}`);
      localStorage.setItem('app_bg', bg);
      bgOptions.forEach(opt => {
        if (opt.dataset.value === bg) opt.classList.add('selected');
        else opt.classList.remove('selected');
      });
    }
  }

  function applyZoneFont(zoneName, family, size) {
    const zone = FONT_ZONES[zoneName];
    if (!zone) return;

    if (family) {
      document.documentElement.style.setProperty(zone.familyVar, family);
      localStorage.setItem(zone.storageFamilyKey, family);
      if (zone.familyEl) zone.familyEl.value = family;
    }
    if (size) {
      document.documentElement.style.setProperty(zone.sizeVar, size);
      localStorage.setItem(zone.storageSizeKey, size);
      if (zone.sizeEl) zone.sizeEl.value = size;
    }
  }

  function applyTypography(typographyConfig) {
    const cfg = typographyConfig || {};
    Object.keys(FONT_ZONES).forEach(zoneName => {
      const zone = FONT_ZONES[zoneName];
      if (!zone) return;
      const savedFamily = (cfg[zoneName] && cfg[zoneName].family) || localStorage.getItem(zone.storageFamilyKey) || (zone.familyEl && zone.familyEl.options.length ? zone.familyEl.options[0].value : "system-ui, -apple-system, 'Segoe UI', sans-serif");
      const savedSize = (cfg[zoneName] && cfg[zoneName].size) || localStorage.getItem(zone.storageSizeKey) || DEFAULT_FONT_SIZE;
      applyZoneFont(zoneName, savedFamily, savedSize);
    });
  }

  // --- 2. 濠电姷鏁告慨鐑藉极閹间礁纾绘繛鎴欏灪閸嬨倝鏌曟繛鐐珔闁告艾缍婇獮鏍庨鈧俊鑲╃棯閹呯Ш闁哄瞼鍠栭幃娆擃敆閳ь剟宕濈捄琛℃斀妞ゆ梻鍘ч弳閬嶆婢舵劖鐓熼柟鎹愭珪閹癸綁鏌熼悾灞解枅闁哄矉缍侀獮鎺楀箣椤撶姴鎮戦梻浣告惈閻鎹㈠┑鍡欐殾闁绘梻鈷堥弫鍐煏閸繃绁╅柛鐐存そ濮婂搫效閸パ呭姶闂佹悶鍔嶅妯跨亱濠电娀娼ч鍛存嫅閻斿吋鐓忓┑鐐茬仢閸旀淇婇幓鎺斿缂佺粯鐩畷鍗炍熼搹閫涙闂備胶顢婄亸娆撳吹閻?闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偛顦甸弫宥夊礋椤掍焦顔囬梻浣告贡閸庛倝宕靛顑炴椽顢旈崨顔界彇闂備線鈧偛鑻晶鎾煙?---
  function switchTab(targetId) {
    tabButtons.forEach(btn => {
      if (btn.dataset.target === targetId) btn.classList.add('active');
      else btn.classList.remove('active');
    });
    tabPanes.forEach(pane => {
      if (pane.id === targetId) pane.classList.add('active');
      else pane.classList.remove('active');
    });
  }

  // --- 3. 闂傚倸鍊搁崐鎼佸磹瀹勬噴褰掑炊瑜滃ù鏍煏婵炵偓娅嗛柛銈呭閺屻倗绮欑捄銊ょ驳濠电偛鎳愭慨鍨┍婵犲洤围闁稿本鐭竟鏇㈡⒒娴ｉ涓茬紒韫矙閹ê顫濈捄铏诡唵闂佸憡绋戦悺銊╁磻閿熺姵鐓欐繛鍫濈仢閺嬨倝鏌ｅ☉鍗炴珝婵﹦绮幏鍛村川婵犲倹娈樻繝鐢靛仩椤曟粎绮婚幘宕囨殾闁靛骏绱曢々鐑芥倵閿濆簼绨介柨娑欑懇濮婅櫣绱掑Ο鍝勵潕闂佺绨洪崐婵嬪箖閿熺姴唯闁挎柨澧介鏇㈡⒑閻熼偊鍤熼柛瀣枛楠炲﹪宕卞Δ濠勫數闁荤喐鐟ョ€氭悂鎳撻崸妤佺厸閻忕偠顕ф俊濂告煃鐟欏嫬鐏寸€规洜鍘ч埞鎴﹀川椤曞懏缍楅梻浣筋嚙濮橈箓锝炴径濞掑搫顫滈埀顒勫Υ閸愨晝绡€闁稿本绮嶅▓楣冩⒑闂堟单鍫ュ疾濠婂牆鍚归悗锝庡亖娴滄粓鏌熸潏鍓хɑ妞ゃ儱顦湁婵犲﹤鐗忛悾娲煛鐏炲墽娲存鐐叉喘濡啫鈽夊▎鎴滈偗缂傚倷鑳堕搹搴ㄥ储閹间礁纾?---
  function populateForm(settings) {
    currentSettings = settings;
    const ui = settings.ui || {};
    applyVisuals(ui.theme || 'dark', ui.background || 'grid');
    applyTypography(ui.typography || {});

    postprocessingRulesEl.value = JSON.stringify(settings.text && settings.text.post_processing_rules ? settings.text.post_processing_rules : [], null, 2);

    const summary = settings.summary || {};
    summaryEnabledEl.checked = !!summary.enabled;
    summaryProfileIdEl.value = summary.profile_id || "";
    summaryFrequencyEl.value = summary.scene_frequency || 1;
    summaryRagConfigEl.value = JSON.stringify(summary.rag_config || {}, null, 2);

    const variables = settings.variables || {};
    variablesEnabledEl.checked = !!variables.enabled;
    variablesProfileIdEl.value = variables.profile_id || "";
    variablesApiConfigIdEl.value = variables.api_config_id || "";
    alignmentStrictEl.checked = !!variables.alignment_strict;
    alignmentRuleIdEl.value = variables.alignment_rule_id || "";

    const textopt = settings.text_opt || {};
    textoptEnabledEl.checked = !!textopt.enabled;
    textoptProfileIdEl.value = textopt.profile_id || "";

    const evolution = settings.world_evolution || {};
    worldEvolutionEnabledEl.checked = !!evolution.enabled;
    worldEvolutionProfileIdEl.value = evolution.profile_id || "";

    const defaults = settings.default_profiles || {};
    defaultProfilesEl.value = JSON.stringify(defaults, null, 2);
  }

  // --- 4. 闂傚倸鍊搁崐鎼佸磹瀹勬噴褰掑炊瑜滃ù鏍煏婵炵偓娅嗛柛銈呭閺屻倗绮欑捄銊ょ驳濠电偛鎳愭慨鍨┍婵犲洤围闁稿本鐭竟鏇㈡⒒娴ｉ涓茬紒韫矙閹ê顫濈捄铏诡唵闂佸憡绋戦悺銊╁磻閿熺姵鐓欐繛鍫濈仢閺嬨倝鏌ｅ☉鍗炴珝婵﹦绮幏鍛村川婵犲倹娈樻繝鐢靛仩椤曟粎绮婚幘宕囨殾闁靛骏绱曢々鐑芥倵閿濆簼绨介柨娑欑懇濮婅櫣绱掑Ο鍝勵潕闂佺绨洪崐婵嬪箖閿熺姴唯闁挎柨澧介鏇㈡⒑閻熼偊鍤熼柛瀣枛楠炲﹪宕ㄩ杞扮盎闂佹寧绻傚Λ娑㈠矗閳ь剟姊洪崫鍕槵闁告挻绻堥獮蹇涘川閺夋垳绱堕梺闈涱樈閻忔繈濡搁妷銏℃杸濡炪倖姊婚妴瀣啅閵夛妇绠鹃悘蹇旂墤閸嬫挸鐣烽崶銊︻啎闂備礁鎲￠〃鍫ュ磿閹邦剦鐒介柍鍝勬噺閻撳繐顭跨捄铏瑰闁诲繆鏅涢湁婵犲﹤鐗忛悾娲煛鐏炲墽娲存鐐叉喘濡啫鈽夊▎鎴滈偗缂傚倷鑳堕搹搴ㄥ储閹间礁纾?---
  function collectForm() {
    const activeThemeEl = document.querySelector('#theme-grid .visual-option.selected');
    const activeBgEl = document.querySelector('#bg-grid .visual-option.selected');
    const themeVal = activeThemeEl ? activeThemeEl.dataset.value : 'dark';
    const bgVal = activeBgEl ? activeBgEl.dataset.value : 'grid';

    const safeParse = (el, name) => {
      try {
        return el.value.trim() ? JSON.parse(el.value) : (name === 'rules' ? [] : {});
      } catch (e) {
        alert(`${name} 的 JSON 格式无效。`);
        throw e;
      }
    };

    let postRules, ragConfig, defaultProfiles;
    try {
      postRules = safeParse(postprocessingRulesEl, 'rules');
      ragConfig = safeParse(summaryRagConfigEl, 'rag');
      defaultProfiles = safeParse(defaultProfilesEl, 'profiles');
    } catch (e) {
      return null;
    }

    const typography = {};
    Object.keys(FONT_ZONES).forEach(zoneName => {
      const zone = FONT_ZONES[zoneName];
      if (!zone || !zone.familyEl || !zone.sizeEl) return;
      typography[zoneName] = {
        family: zone.familyEl.value,
        size: zone.sizeEl.value
      };
    });

    return {
      ui: {
        theme: themeVal,
        background: bgVal,
        typography
      },
      text: {
        post_processing_rules: postRules
      },
      summary: {
        enabled: summaryEnabledEl.checked,
        profile_id: summaryProfileIdEl.value.trim(),
        scene_frequency: parseInt(summaryFrequencyEl.value || "1", 10),
        rag_config: ragConfig
      },
      variables: {
        enabled: variablesEnabledEl.checked,
        profile_id: variablesProfileIdEl.value.trim(),
        api_config_id: variablesApiConfigIdEl.value.trim(),
        alignment_strict: alignmentStrictEl.checked,
        alignment_rule_id: alignmentRuleIdEl.value.trim()
      },
      text_opt: {
        enabled: textoptEnabledEl.checked,
        profile_id: textoptProfileIdEl.value.trim()
      },
      world_evolution: {
        enabled: worldEvolutionEnabledEl.checked,
        profile_id: worldEvolutionProfileIdEl.value.trim()
      },
      default_profiles: defaultProfiles
    };
  }

  // --- 5. API 濠电姷鏁告慨鐑藉极閹间礁纾绘繛鎴欏灪閸嬨倝鏌曟繛鐐珔闁告艾缍婇獮鏍庨鈧俊鑲╃棯閹呯Ш闁哄瞼鍠栭幃娆擃敆閳ь剟宕濈捄琛℃斀?---
  async function loadSettings() {
    statusEl.textContent = "正在加载...";
    try {
      const resp = await window.authFetch("/api/settings/global");
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();
      populateForm(data);
      statusEl.textContent = "已加载";
      setTimeout(() => statusEl.textContent = "就绪", 2000);
    } catch (err) {
      console.error(err);
      statusEl.textContent = "加载失败";
    }
  }

  async function saveGlobalSettings(keys) {
    const settings = collectForm();
    if (!settings) return false;

    if (keys.includes("ui")) {
      applyVisuals(settings.ui.theme, settings.ui.background);
      applyTypography(settings.ui.typography || {});
    }

    statusEl.textContent = "濠电姷鏁搁崕鎴犲緤閽樺娲晜閻愵剙搴婇梺绋跨灱閸嬬偤宕戦妶澶嬬厪濠电姴绻愰々顒勬煃?..";
    const payload = mergeSettingsByKeys(currentSettings, settings, keys);

    try {
      const resp = await window.authFetch("/api/settings/global", {
        method: "PUT",
        body: JSON.stringify(payload)
      });
      if (!resp.ok) {
        console.error("Failed to save global settings");
        statusEl.textContent = "保存失败";
        setTimeout(() => statusEl.textContent = "就绪", 2000);
        return false;
      }

      currentSettings = payload;
      statusEl.textContent = "已保存";
      setTimeout(() => statusEl.textContent = "就绪", 2000);
      return true;
    } catch (err) {
      console.error(err);
      statusEl.textContent = "保存失败";
      setTimeout(() => statusEl.textContent = "就绪", 2000);
      return false;
    }
  }

  async function saveSettings() {
    const activeTabId = getActiveTabId();
    const globalKeys = GLOBAL_TAB_KEY_MAP[activeTabId];

    if (globalKeys) {
      return saveGlobalSettings(globalKeys);
    }

    statusEl.textContent = "濠电姷鏁搁崕鎴犲緤閽樺娲晜閻愵剙搴婇梺绋跨灱閸嬬偤宕戦妶澶嬬厪濠电姴绻愰々顒勬煃?..";

    try {
      if (activeTabId === "tab-presets" && typeof window.savePresetChanges === 'function') {
        await window.savePresetChanges();
      } else if (activeTabId === "tab-regex" && typeof window.saveCurrentRegex === 'function') {
        await window.saveCurrentRegex();
      } else if (activeTabId === "tab-api" && typeof window.saveCurrentLLMConfig === 'function') {
        await window.saveCurrentLLMConfig();
      } else {
        statusEl.textContent = "Nothing to save for this tab";
        setTimeout(() => statusEl.textContent = "就绪", 2000);
        setTimeout(() => statusEl.textContent = "就绪", 2000);
      }

      statusEl.textContent = "已保存";
      statusEl.textContent = "已保存";
      setTimeout(() => statusEl.textContent = "就绪", 2000);
    } catch (err) {
      console.error("濠电姷鏁搁崕鎴犲緤閽樺娲晜閻愵剙搴婇梺绋跨灱閸嬬偤宕戦妶澶嬬厪濠电偛鐏濇俊绋棵瑰鍐Ш闁哄瞼鍠栭獮鍡氼槻闁哄棜椴搁妵鍕Χ閸涱喖娈楅梺鍝勬湰閻╊垶鐛幒妤€绠ｉ柣鎴濇閿涘棝姊绘笟鈧褍螞濡ゅ惤鍥级濞嗘儳娈梺鍛婃处閸撴氨绱為崶銊ｄ簻闁规壋鏅涢崜?", err);
      statusEl.textContent = "保存失败";
      setTimeout(() => statusEl.textContent = "就绪", 2000);
      setTimeout(() => statusEl.textContent = "就绪", 2000);
    }
  }
  // --- 6. 濠电姷鏁告慨鐑藉极閹间礁纾绘繛鎴欏灪閸嬨倝鏌曟繛褍鍟悘濠囨倵閸忓浜鹃梺鍛婃礀閻忔岸寮查悙鐑樷拺闁告稑锕ユ径鍕煕鐎Ｑ冧壕闂備礁鎼鍛存煀閿濆钃熼柡鍥风磿閻も偓闁诲函缍嗘禍鐐村閸曨厾纾奸柣鎰靛墮閸斻倝鏌曢崼鐔稿€愮€殿喖顭烽幃銏㈡偘閳ュ厖澹曞┑鐐村灦閻燁垶鎮為悾宀€纾奸柣妯碱劜閼板潡鏌?---
  function bindEvents() {
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => switchTab(btn.dataset.target));
    });

    themeOptions.forEach(opt => {
      opt.addEventListener('click', () => {
        applyVisuals(opt.dataset.value, null);
      });
    });

    bgOptions.forEach(opt => {
      opt.addEventListener('click', () => {
        applyVisuals(null, opt.dataset.value);
      });
    });

    // 闂傚倸鍊搁崐宄懊归崶顒夋晪鐟滃繘鍩€椤掍胶鈻撻柡鍛箘閸掓帒鈻庨幘宕囶唺濠德板€愰崑鎾愁浖閸涘瓨鈷戠紓浣姑慨澶愭煛娴ｅ憡鎲哥紒顔肩墛缁绘繈宕堕妸銉㈠亾閻㈠憡鐓ユ繝闈涙椤庢鏌＄€ｎ剙鏋涢柡灞剧⊕閹棃鍩勯崘鈺侀棷缂傚倷娴囨ご鍝ユ暜閻愬搫鐒垫い鎺戯功缁夐潧霉濠婂懎浠︾紒鍌涘浮婵偓闁靛繆鈧櫕鐎鹃梻浣筋潐椤旀牠宕伴弽褎姣勭紓鍌氬€峰ù鍥ㄣ仈閹间礁绠板┑鐘宠壘缁狀垶鏌涘☉妯兼憼闁稿绻濋弻鐔封枔閸喗鐏嗗┑鐑囩秵閸ｏ絽顫?
    [fontUiFamilyEl, fontUiSizeEl, fontStoryFamilyEl, fontStorySizeEl,
     fontConsoleFamilyEl, fontConsoleSizeEl, fontCharFamilyEl, fontCharSizeEl,
     fontWorldFamilyEl, fontWorldSizeEl, fontDungeonFamilyEl, fontDungeonSizeEl].forEach(el => {
       if(el) {
         el.addEventListener('change', () => applyTypography(collectForm()?.ui?.typography));
       }
    });

    // 闂傚倸鍊峰ù鍥敋瑜忛埀顒佺▓閺呯娀銆佸▎鎾冲唨妞ゆ挾鍋熼悰銉╂⒑閸︻厼鍔嬫い銊ユ噽婢规洘绻濆顓犲幍闂佸憡鎸嗛崨顓狀偧闂備胶绮幐璇裁哄Ο鍏煎床婵炴垯鍨归獮銏′繆椤栨碍鎯堟い顐㈢焸濮婅櫣鎷犻懠顒傤啋婵炲瓨绮岄悥鐓庮嚕鐠囧樊鍚嬮柛顐亝椤庡洭姊绘担鍛婂暈闁圭顭烽幃鐑藉煛閸涱垰绁︽繝鐢靛Т閹虫劙鎮块埀顒€鈹戦鏂や緵闁告挻鑹鹃埢鎾诲蓟閵夛腹鎷洪柣鐘叉处瑜板啴顢楅姀掳浜滈柡鍐ｅ亾闁绘濮撮悾閿嬪閺夋垵鍞ㄥ銈嗗姧缁茶姤鎯旀繝鍥ㄢ拺鐟滅増甯掓禍浼存煕閻樻剚娈滈柨婵堝仱瀵挳濮€閿涘嫬骞嶉梺鍝勵槸閻楀棙鏅舵禒瀣仼閺夊牃鏅濈壕濂告煃?
    const devModeCheckbox = document.getElementById('developer-mode-enabled');
    if (devModeCheckbox) {
      devModeCheckbox.checked = localStorage.getItem('developer_mode_enabled') === 'true';
      devModeCheckbox.addEventListener('change', function() {
        localStorage.setItem('developer_mode_enabled', this.checked ? 'true' : 'false');
        if (typeof window.DevTools !== 'undefined') {
          window.DevTools.setDeveloperMode(this.checked);
        }
      });
    }

    loadBtn.addEventListener("click", loadSettings);
    saveBtn.addEventListener("click", saveSettings);
  }

  // --- 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偛顦甸弫宥夊礋椤掍焦顔囨繝寰锋澘鈧洟宕姘辨殾闁哄被鍎查悡鏇犫偓鍏夊亾闁逞屽墴瀹曟洟骞嬮悩鐢殿槸闂佸搫绋侀崢浠嬫偂濞嗘挻鐓熸俊銈傚亾闁绘锕﹀▎銏ゆ嚑椤掑倻锛滈梺?---
  function init() {
    initAuthUI();
    bindEvents();
    loadSettings();
  }
  
  function initAuthUI() {
    const usernameEl = document.getElementById('nav-username');
    const logoutBtn = document.getElementById('nav-logout-btn');
    const loginLink = document.getElementById('nav-login-link');
    
    if (typeof Auth !== 'undefined') {
      Auth.updateUserUI(usernameEl, logoutBtn);
      
      if (logoutBtn) {
        logoutBtn.addEventListener('click', () => Auth.logout());
      }
      
      const user = Auth.getUser();
      if (user && loginLink) {
        loginLink.style.display = 'none';
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.saveSettingsByActiveTab = saveSettings;
})();

/* =========================================================
 * 濠电姷鏁告慨鐑姐€傞挊澹╋綁宕ㄩ弶鎴狅紱闂佸憡渚楅崣搴ㄦ偄閸℃ü绻嗘い鏍ㄦ皑濮ｇ偤鏌涚€ｎ偅灏い顐ｇ箞閹剝鎯旈敐鍕敇濠碉紕鍋戦崐鎴﹀垂濞差亝鍋￠柍杞扮贰閸ゆ洟鏌熺紒銏犳灍闁稿鍔欓弻娑滅疀閹惧瓨鍠愰梺鑽ゅ枑缁诲牆顫忕紒妯诲闁荤喖鍋婇崵瀣磽娴ｅ壊鍎愰柛銊ョ秺閸┾偓妞ゆ帊绀侀崵顒勬煕濞嗗繐鏆欓柣?+ API闂傚倸鍊搁崐鎼佸磹閹间礁纾归柣鎴ｅГ閸婂潡鏌ㄩ弴妤€浜惧銈庡幖閻忔繆鐏掗梺鍏肩ゴ閺呮繈鎮＄€ｎ喗鈷戦柛鎾村絻娴滄繃绻涢崣澶涜€跨€规洘鍨块、鏃堝醇閻斿搫骞堥梻浣规灱閺呮盯宕导鏉戠厐闁哄洢鍨洪悡娑㈡煕濠娾偓缁€浣规櫠閹绢喗鐓涢悘鐐插⒔濞插瓨銇勯姀鈩冪闁轰焦鍔欏畷鍫曞煛閸愵亞宕跺┑鐘垫暩閸嬫盯鎮洪妸褍鍨濋柨婵嗘搐缁躲倝鏌ｉ幇闈涘闁崇懓绉撮埞鎴︽偐閸欏銈╅梺杞扮缁夊灚绌辨繝鍥ㄥ€峰Λ鐗堢箓濞堫厽绻涚€涙鐭婂褌绮欓崺鈧い鎺戝枤濞兼劖绻涢崣澶屽ⅹ閻撱倝鏌ｅΟ娆惧殭缁炬儳顭烽弻鐔煎礈瑜忕敮娑㈡煕婵犲偆鐓奸柡灞诲€濋獮渚€骞掗幋婵嗩潥婵?- 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈡晜閽樺缃曟繝鐢靛Т閿曘倝鎮ч崱娆戠焼闁割偆鍠愰崣蹇旀叏濡炶浜惧銈冨€曢崐鍨嚕椤愶箑绀冮柕濞垮灪閺傗偓闂備胶顭堥張顒傚枈瀹ュ鐤柣鎰劋閻撶喖鏌熼幆褍鏆遍柍褜鍓欓…鐑藉春閳ь剚銇勯幒鍡椾壕缂備胶濮寸粔鐟扮暦閺囥垹纭€闁绘劕绉电粙鎴﹀煡婢舵劕顫呴柣姗€娼ф慨锔戒繆閻愵亜鈧牜鏁幒妞濆洭顢涢悙鏉戔偓鍫曟煥閺冨牊鏆滈柛瀣尭閳绘捇宕归鐣屽蒋闂備礁鎲￠幐楣冨窗鎼搭煈鏁嬮柨婵嗘处瀹曞鎮跺☉鎺戝⒉闁诲骸顭峰铏圭磼濡搫袝闂佸憡鎸诲銊モ枎?
 * ========================================================= */
(function () {
  // --- 闂傚倸鍊搁崐宄懊归崶顒夋晪鐟滃繘骞戦姀銈呯疀妞ゆ棁妫勬惔濠囨⒑瑜版帒浜伴柛鐘愁殔閻ｇ兘寮婚妷锔惧幍闂備緡鍙忕粻鎴︾嵁閺嶃劊浜滈柡鍥舵線閹查箖鏌″畝鈧崰鏍箖瑜斿畷濂告偄閸濆嫬娈ョ紓鍌氬€风拋鏌ュ磻?---
  const $ = (id) => document.getElementById(id);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function nowId(prefix) {
    return prefix + "_" + Math.random().toString(16).slice(2, 10);
  }

  function setText(el, text) {
    if (!el) return;
    el.textContent = text;
  }

  async function safeJson(resp) {
    const ct = (resp.headers.get("content-type") || "").toLowerCase();
    if (ct.includes("application/json")) return await resp.json();
    const t = await resp.text();
    try { return JSON.parse(t); } catch (e) { return { raw: t }; }
  }

  // =========================================================
  // A) 濠电姷鏁告慨鐑姐€傞挊澹╋綁宕ㄩ弶鎴狅紱闂佸憡渚楅崣搴ㄦ偄閸℃ü绻嗘い鏍ㄦ皑濮ｇ偤鏌涚€ｎ偅灏い顐ｇ箞閹剝鎯旈敐鍕敇濠碉紕鍋戦崐鎴﹀垂濞差亝鍋￠柍杞扮贰閸ゆ洟鏌熺紒銏犳灍闁稿鍔欓弻娑滅疀閹惧瓨鍠愰梺鑽ゅ枑缁诲牆顫忕紒妯诲闁荤喖鍋婇崵瀣磽娴ｅ壊鍎愰柛銊ョ秺閸┾偓妞ゆ帊绀侀崵顒勬煕濞嗗繐鏆欓柣?
  // =========================================================
  const presetSelectEl = $("preset-select");
  const presetActiveHintEl = $("preset-active-hint");
  const presetStatusEl = $("preset-status");

  const presetCreateBtn = $("preset-create-btn");
  const presetSetActiveBtn = $("preset-set-active-btn");
  const presetRenameBtn = $("preset-rename-btn");
  const presetDeleteBtn = $("preset-delete-btn");

  const presetImportFileEl = $("preset-import-file");
  const presetExportBtn = $("preset-export-btn");

  const presetTreeEl = $("preset-tree");
  const addGroupBtn = $("preset-add-group-btn");
  const addPromptBtn = $("preset-add-prompt-btn");
  const deleteNodeBtn = $("preset-delete-node-btn");

  // 缂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾惧綊鏌熼梻瀵割槮缁炬儳婀遍幉鎼佹偋閸繄鐟查梺绋款儏椤戝寮婚敐澶婄疀妞ゆ帒鍊风划闈涱渻閵堝棗濮屽┑顔哄€濇俊鐢稿礋椤栨氨鐤€闂佸憡鎸烽懗鍫曞汲閻樼粯鈷掗柛灞捐壘娴滅偤鏌涢妸銉у煟鐎殿喖顭峰鎾偄閾忚鍟庨梻浣稿閻撳牓宕伴弽銊﹀弿闁靛繈鍊栭埛鎴︽煕閿旇骞楁繛鍛礋閺屾盯鎮╅崘鎻掝潕闂?
  const nodeTitleEl = $("preset-node-title");
  const nodeEnabledEl = $("preset-node-enabled");
  const nodeIdentifierEl = $("preset-node-identifier");
  const nodeOrderEl = $("preset-node-order");

  const nodePromptFieldsEl = $("preset-node-prompt-fields");
  const nodeRoleEl = $("preset-node-role");
  const nodeContentEl = $("preset-node-content");
  const nodeHintEl = $("preset-node-hint");

  const nodeDepthEl = $("preset-node-depth");
  const nodePositionEl = $("preset-node-position");
  const nodeSystemPromptEl = $("preset-node-system-prompt");
  const nodeMarkerEl = $("preset-node-marker");
  const nodeOverridesEl = $("preset-node-overrides");
  const nodeTriggersEl = $("preset-node-triggers");
  const promptOnlyTogglesEl = $("prompt-only-toggles");
  const editorContainerEl = $("preset-node-editor-container");

  let presetsOverview = [];
  let activePresetId = null;
  let currentPreset = null;  // full preset
  let selectedNodeId = null;
  let parentMap = {}; // nodeId -> parentId
  
  // 濠电姷鏁告慨鐑藉极閹间礁纾块柟瀵稿Т缁躲倝鏌﹀Ο渚＆鐟滅増甯掔壕濂告煟閹邦垰鐨洪柣娑栧劚閳规垶骞婇柛濠冩礋楠炲﹥鎯旈妸銉ュ殤婵炴挻鍩冮崑鎾绘煛鐏炶鈧洟婀侀柣搴秵閸嬪懘鎮甸弴銏″€甸悷娆忓缁€鈧銈忓閺佽顕ｆ繝姘櫜濠㈣泛锕ラˉ婵嗏攽閻愬弶顥滃褌绮欏畷銉р偓锝庡枟閳锋垿鏌熼懖鈺佷粶闁逞屽墯濞茬喖銆侀弽銊ョ窞闁归偊鍓濋幗鏇㈡⒑閹稿海绠撻柟鍙夛耿閹垽鎮℃惔锛勨偓顓烆渻閵堝棙鈷愰柛搴＄－閺侇噣宕稿Δ浣叉嫽?
  let presetModified = false;
  let modifiedNodes = new Set();

  function buildParentMap(node, parentId) {
    if (!node || typeof node !== "object") return;
    if (node.id) parentMap[node.id] = parentId || null;
    if (node.kind === "group" && Array.isArray(node.children)) {
      for (const ch of node.children) buildParentMap(ch, node.id);
    }
  }

  function findNode(node, id) {
    if (!node || typeof node !== "object") return null;
    if (node.id === id) return node;
    if (node.children && Array.isArray(node.children)) {
      for (const ch of node.children) {
        const found = findNode(ch, id);
        if (found) return found;
      }
    }
    return null;
  }

  function findParent(node, id) {
    const pid = parentMap[id];
    if (!pid) return null;
    return findNode(node, pid);
  }

  function renderTree() {
    if (!presetTreeEl) return;

    if (!currentPreset || !currentPreset.root) {
        presetTreeEl.innerHTML = '<div style="padding:20px; text-align:center; color:#666;">请选择一个预设，或先复制/新建预设后开始编辑。</div>';
        return;
    }

    presetTreeEl.innerHTML = "";
    parentMap = {};
    buildParentMap(currentPreset.root, null);

    const root = currentPreset.root;

    function renderNode(node, depth) {
      if (!node) return;

      const row = document.createElement("div");
      row.className = "config-tree-node";
      if (selectedNodeId && node.id === selectedNodeId) {
          row.classList.add("selected");
      }
      if (node.enabled === false) {
          row.classList.add("disabled");
      }

      row.style.paddingLeft = (depth * 18 + 8) + "px";

      const toggleLabel = document.createElement("label");
      toggleLabel.className = "toggle-switch";
      toggleLabel.style.transform = "scale(0.7)";
      toggleLabel.style.margin = "0";
      toggleLabel.onclick = (e) => e.stopPropagation();

      const input = document.createElement("input");
      input.type = "checkbox";
      input.checked = node.enabled !== false;
      input.onchange = () => {
          node.enabled = input.checked;
          if (selectedNodeId === node.id && nodeEnabledEl) {
              nodeEnabledEl.checked = input.checked;
          }
          renderTree();
      };

      const slider = document.createElement("span");
      slider.className = "slider";
      toggleLabel.appendChild(input);
      toggleLabel.appendChild(slider);

      const icon = document.createElement("span");
      icon.className = "tree-icon";
      icon.textContent = node.kind === "group" ? "[]" : "{}";

      const titleDiv = document.createElement("div");
      titleDiv.className = "tree-title";
      titleDiv.textContent = node.title || node.identifier || "Untitled";

      if (node.kind === "prompt") {
          const infoDiv = document.createElement("span");
          infoDiv.className = "small-text muted";
          infoDiv.style.fontSize = "11px";
          infoDiv.style.marginLeft = "auto";
          infoDiv.textContent = `#${node.injection_order || 0}`;
          row.appendChild(toggleLabel);
          row.appendChild(icon);
          row.appendChild(titleDiv);
          row.appendChild(infoDiv);
      } else {
          row.appendChild(toggleLabel);
          row.appendChild(icon);
          row.appendChild(titleDiv);
      }

      row.addEventListener("click", () => {
        selectedNodeId = node.id;
        renderTree();
        syncEditor();
      });

      presetTreeEl.appendChild(row);

      if (node.kind === "group" && Array.isArray(node.children)) {
        node.children.forEach(child => {
            if(child) renderNode(child, depth + 1);
        });
      }
    }

    renderNode(root, 0);
  }

  function syncEditor() {
    const container = editorContainerEl;
    const hint = nodeHintEl;

    if (!currentPreset || !selectedNodeId) {
      if(container) container.style.display = "none";
      if(hint) hint.style.display = "flex";
      return;
    }

    const node = findNode(currentPreset.root, selectedNodeId);
    if (!node) {
      console.warn("闂傚倸鍊搁崐鎼佸磹閹间礁纾瑰瀣椤愪粙鏌ㄩ悢鍝勑㈢痪鎯ь煼閺屾盯寮撮妸銉р偓顒勬煕閵夘喖澧婚柡浣割儔閺屽秷顧侀柛鎾跺枛閻涱喗绻濋崒妤佺€婚梺瑙勫劤绾绢參顢樺ú顏呪拺闁圭瀛╅ˉ鍡樹繆椤愩垹顏€规洘绮撻、姗€濮€閳锯偓閹锋椽姊洪崨濠勨槈闁挎洏鍎插鍕礋椤栨稓鍘遍梺缁樏壕顓熸櫠閹惰姤鐓熼煫鍥ㄦ煥婵秵鎱?ID 闂傚倸鍊搁崐鎼佸磹妞嬪孩顐芥慨姗嗗墻閻掍粙鏌ゆ慨鎰偓鏍偓姘煼閺岋綁寮崒姘粯缂備讲鍋撳璺哄閸嬫捇鐛崹顔煎濡炪倧缂氶崡鍐茬暦閹寸偛绶為柟閭﹀幘閸樺崬鈹戦悙鍙夘棞婵炲瓨鑹惧嵄婵炲樊浜濋悡鍐磽娴ｈ偂鎴﹀煕閹扮増鐓忛柛銉戝喚浼冨Δ鐘靛仦椤洭骞戦崟顖涘€绘俊顖氱毞閸嬫挻銈ｉ崘鈺佲偓鍨箾閸繄浠㈤柡瀣枛閺岀喖鎮烽悧鍫濇灎閻庢鍠栭…鐑藉箖閵忋倖鍋傞幖杈剧磿閳ь剦鍘奸—鍐Χ閸℃顫囬梺鎼炲姀椤骞堥妸鈺侇潊闁靛牆妫岄幏?", selectedNodeId);
      return;
    }

    if(container) container.style.display = "flex";
    if(hint) hint.style.display = "none";

    // 闂傚倸鍊搁崐鎼佸磹閻戣姤鍊块柨鏇炲€哥粻鏍煕椤愶絾绀€缁炬儳娼￠弻鐔煎箚閻楀牜妫勭紒鐐劤椤兘寮婚敐澶婄疀妞ゆ巻鍋撴俊顐ｏ耿閺岋綁寮崒銈囧姼缂備礁澧庨崑銈夊蓟閻斿吋鐒介柨鏇楀亾妤犵偞锕㈤弻娑㈠籍閸喐閿梺瀹狀潐閸ㄥ潡銆佸▎鎴犻┏閻庯綆鍓欐慨鐓庘攽閿涘嫬浠滈柣掳鍔戦獮鍐磼濮樼厧娈ㄩ柣搴℃贡婵兘鎮块埀顒€鈹戦悙鏉戠仸闁荤啙鍥у偍闁告稑锕︾粻楣冨级閸繂鈷旈柛鎺嶅嵆閺岀喓鍠婇崡鐐板枈闂侀潧妫楅崐鍧楀箠閺嶎厼鐓橀柟顖嗗倸顥?
    if(nodeTitleEl) nodeTitleEl.value = node.title || node.name || "";
    if(nodeIdentifierEl) nodeIdentifierEl.value = node.identifier || "";
    if(nodeEnabledEl) nodeEnabledEl.checked = node.enabled !== false;

    const isGroup = node.kind === "group" || Array.isArray(node.children);

    const promptFields = $("preset-node-prompt-fields");
    const groupHint = $("prompt-bool-fields");

    if (isGroup) {
      if(promptFields) promptFields.style.display = "none";
      if(groupHint) groupHint.style.display = "flex";
    } else {
      if(promptFields) promptFields.style.display = "flex";
      if(groupHint) groupHint.style.display = "none";

      if(nodeContentEl) nodeContentEl.value = node.content || "";
      if(nodeRoleEl) nodeRoleEl.value = node.role || "system";
      if(nodePositionEl) nodePositionEl.value = node.injection_position || 0;
      if(nodeOrderEl) nodeOrderEl.value = node.injection_order || 0;
      if(nodeDepthEl) nodeDepthEl.value = node.injection_depth || 0;

      if(nodeSystemPromptEl) nodeSystemPromptEl.checked = !!node.system_prompt;
      if(nodeMarkerEl) nodeMarkerEl.checked = !!node.marker;
      if(nodeOverridesEl) nodeOverridesEl.checked = !!node.forbid_overrides;

      if(nodeTriggersEl) nodeTriggersEl.value = (node.injection_trigger || []).join(", ");
    }
  }

  function updateSaveButtonState() {
    const saveBtn = document.getElementById('settings-save-btn');
    if (saveBtn) {
      if (presetModified) {
        saveBtn.textContent = '保存更改 *';
        saveBtn.style.background = 'var(--accent)';
      } else {
        saveBtn.textContent = '保存更改';
        saveBtn.style.background = '';
      }
    }
  }

  function bindPresetEditorEvents() {
    const updateNode = (key, val) => {
      const node = selectedNodeId ? findNode(currentPreset.root, selectedNodeId) : null;
      if (!node) return;
      
      // 婵犵數濮烽弫鍛婃叏閻戝鈧倿鎸婃竟鈺嬬秮瀹曘劑寮堕幋鐙呯幢闂備線鈧偛鑻晶鎾煛鐏炲墽銆掗柍褜鍓ㄧ紞鍡涘磻閸涱厾鏆︾€光偓閸曨剛鍘搁悗鍏夊亾閻庯綆鍓涢敍鐔哥箾鐎电顎撳┑鈥虫喘楠炲繘鎮╃拠鑼唽闂佸湱鍎ら崺鍫濐焽濞戙垺鈷掗柛灞剧懅缁愭棃鏌嶈閸撴盯宕戝☉銏″殣妞ゆ牗绋掑▍鐘炽亜閺囨浜鹃梺鍝勬湰缁嬫垿锝炲┑瀣垫晢濠㈣泛锕ゆ竟鍫ユ⒑閸涘娈滃ù婊冪埣瀵鎮㈤崗灏栨嫽闁诲酣娼ф竟濠偽ｉ鈧弻锝夋偄閸濄儲鍤傜紓浣哄У閹瑰洤顕ｆ繝姘╅柍杞拌兌閻嫰姊虹粙鎸庢拱闁活収鍠楃粩鐔煎即閵忊檧鎷虹紓渚囧灡濞叉ê鈻嶉崨瀛樼厱濠电姴鍊归崑銉р偓娈垮枛椤兘寮幇顓炵窞濠电偐鎳囬弲鐘诲蓟閺囩喎绶為柛顐ｇ箓婵埖绻涚€电鈻堢紒鐘崇墪椤繘鎮滃Ο璇差潯闂佽顔栭崳顔嘉ｉ鈧娲濞戞艾鈪卞銈庡幖閻楁捇骞冩ィ鍐╁€婚柤鎭掑劜濞呮粓姊洪崨濠勨槈闁稿﹤顭峰畷浼村冀瑜忛弳锕傛煟閹寸姷鎽傞柡浣告喘閺岋綁骞囬鍌涙喖闂?
      const oldValue = node[key];
      if (oldValue === val) return;
      
      node[key] = val;
      
      // 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠Χ閸モ晝鍘犻梻浣告惈椤︿即宕靛顑炴椽顢旈崟顓炲箰闂備礁鎲＄划鍫ユ倿閿曞倸鐤鹃柍鍝勬噺閳锋垿鏌熼懖鈺佷粶闁告梹锕㈤弻娑㈠棘閸ф寮伴梺绯曟杺閸ㄨ棄顕ｉ鈧畷濂告偄閸濆嫬绠炲┑鐘垫暩婵炩偓婵炰匠鍏炬稑螖閸滀焦鏅滈梺鍐叉惈閹冲繘鎮￠弴銏＄厪闁割偅绻冮ˉ婊呯磼濡や礁娴柟绛圭秮楠炲洭鎮ч崼銏犲箞闂備線娼чˇ顓㈠礉瀹ュ洦鍏滃Δ锝呭暞閻撴盯鎮楅敐搴″闁哄鐩弻?
      presetModified = true;
      if (selectedNodeId) {
        modifiedNodes.add(selectedNodeId);
      }
      
      // 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠煕濮橆厽銇濆┑陇鍩栧鍕偓锝庝簷濡叉劙姊绘笟鈧褑澧濋梺鍝勬噺閻╊垶骞忛幋锔藉亜閻忓繋鐒﹂弬鈧梻浣虹帛钃辩憸鏉垮暣瀵娊鎮㈤崗鑲╁帗闂佽崵鍠愭竟鍡樼墡缂傚倷鑳剁划顖滄崲閸惊娑㈠礃閵娿垺顫嶅┑鐐叉钃遍柨鐔村劦濮婄粯鎷呴崨濠呯闂佸搫鎷嬮崑鍛崲濞戙垹鐒垫い鎺戝閻撴稓鈧厜鍋撻柍褜鍓熷畷浼村箻鐠哄搫鐏婂┑鐐叉缁诲棝寮告惔銊︾厽闁逛即娼ч崢鎾煛鐎ｎ亝鍤囨慨濠勭帛閹峰懘鎮滃Ο鐑樼暚闂備浇顫夌粊鎾礈濠靛牊宕叉繛鎴炵懅缁♀偓闂佹悶鍎滈崨顖涙瘒闂傚倷绀侀崯鍧楀箹椤愶箑绠犻煫鍥ㄧ☉閸氬綊鎮楅敐搴″婵☆偒鍨堕弻锝呂旈埀顒勬偂椤愶富鏁傞柛娑卞灱濞?
      updateSaveButtonState();
      
      if (key === 'title' || key === 'identifier' || key === 'enabled') renderTree();
    };

    if(nodeTitleEl) nodeTitleEl.addEventListener("input", () => updateNode('title', nodeTitleEl.value));
    if(nodeIdentifierEl) nodeIdentifierEl.addEventListener("input", () => updateNode('identifier', nodeIdentifierEl.value));
    if(nodeContentEl) nodeContentEl.addEventListener("input", () => updateNode('content', nodeContentEl.value));

    if(nodeOrderEl) nodeOrderEl.addEventListener("change", () => updateNode('injection_order', parseInt(nodeOrderEl.value) || 0));
    if(nodeDepthEl) nodeDepthEl.addEventListener("change", () => updateNode('injection_depth', parseInt(nodeDepthEl.value) || 0));

    if(nodeRoleEl) nodeRoleEl.addEventListener("change", () => updateNode('role', nodeRoleEl.value));
    if(nodePositionEl) nodePositionEl.addEventListener("change", () => updateNode('injection_position', nodePositionEl.value));

    if(nodeEnabledEl) nodeEnabledEl.addEventListener("change", () => {
      updateNode('enabled', nodeEnabledEl.checked);
    });
    if(nodeSystemPromptEl) nodeSystemPromptEl.addEventListener("change", () => updateNode('system_prompt', nodeSystemPromptEl.checked));
    if(nodeMarkerEl) nodeMarkerEl.addEventListener("change", () => updateNode('marker', nodeMarkerEl.checked));
    if(nodeOverridesEl) nodeOverridesEl.addEventListener("change", () => updateNode('forbid_overrides', nodeOverridesEl.checked));

    if(nodeTriggersEl) nodeTriggersEl.addEventListener("change", () => {
      const val = nodeTriggersEl.value;
      const arr = val.split(/[,，]/).map(s => s.trim()).filter(s => s);
      updateNode('injection_trigger', arr);
    });
  }

  function addChildNode(kind) {
    if (!currentPreset) return;
    const root = currentPreset.root;

    let parent = root;
    if (selectedNodeId) {
      const node = findNode(root, selectedNodeId);
      if (node && node.kind === "group") parent = node;
      else {
        const p = findParent(root, selectedNodeId);
        if (p && p.kind === "group") parent = p;
      }
    }
    parent.children = Array.isArray(parent.children) ? parent.children : [];
    
    const newNode = kind === "group" ? {
      id: nowId("node"),
      kind: "group",
      title: "New group",
      enabled: true,
      children: []
    } : {
      id: nowId("node"),
      kind: "prompt",
      title: "New prompt",
      enabled: true,
      role: "system",
      content: ""
    };
    
    parent.children.push(newNode);
    
    // 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠Χ閸モ晝鍘犻梻浣告惈椤︿即宕靛顑炴椽顢旈崟顓炲箰闂備礁鎲＄划鍫ユ倿閿曞倸鐤鹃柍鍝勬噺閳锋垿鏌熼懖鈺佷粶闁告梹锕㈤弻娑㈠棘閸ф寮伴梺绯曟杺閸ㄨ棄顕ｉ鈧畷濂告偄閸濆嫬绠炲┑鐘垫暩婵炩偓婵炰匠鍏炬稑螖閸滀焦鏅滈梺鍐叉惈閹冲繘鎮￠弴銏＄厪闁割偅绻冮ˉ婊呯磼濡や礁娴柟绛圭秮楠炲洭鎮ч崼銏犲箞闂備線娼чˇ顓㈠礉瀹ュ洦鍏滃Δ锝呭暞閻撴盯鎮楅敐搴″闁哄鐩弻?
    presetModified = true;
    modifiedNodes.add(newNode.id);
    updateSaveButtonState();
    
    renderTree();
  }

  function deleteSelectedNode() {
    if (!currentPreset || !selectedNodeId) return;
    const root = currentPreset.root;
    if (root.id === selectedNodeId) {
      alert("根节点不能删除。");
      return;
    }
    const parent = findParent(root, selectedNodeId);
    if (!parent || parent.kind !== "group") return;

    // 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠Χ閸モ晝鍘犻梻浣告惈椤︿即宕靛顑炴椽顢旈崟顓炲箰闂備礁鎲＄划鍫ユ倿閿曞倸鐤鹃柍鍝勬噺閳锋垿鏌熼懖鈺佷粶闁告梹锕㈤弻娑㈠棘閸ф寮伴梺绯曟杺閸ㄨ棄顕ｉ鈧畷濂告偄閸濆嫬绠炲┑鐘垫暩婵炩偓婵炰匠鍏炬稑螖閸滀焦鏅滈梺鍐叉惈閹冲繘鎮￠弴銏＄厪闁割偅绻冮ˉ婊呯磼濡や礁娴柟绛圭秮楠炲洭鎮ч崼銏犲箞闂備線娼чˇ顓㈠礉瀹ュ洦鍏滃Δ锝呭暞閻撴盯鎮楅敐搴″闁哄鐩弻?
    presetModified = true;
    modifiedNodes.add(selectedNodeId);
    
    parent.children = (parent.children || []).filter(ch => ch.id !== selectedNodeId);
    selectedNodeId = parent.id;
    
    updateSaveButtonState();
    renderTree();
    syncEditor();
  }

  async function loadPresetsOverview() {
    if (presetStatusEl) setText(presetStatusEl, "闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偛顦甸崹楣冨箛娴ｅ湱绋佺紓鍌氬€烽悞锕佹懌闂佸憡鐟ョ换姗€寮婚悢纰辨晬闁挎繂娲ｅЧ妤呮偡濠婂懎顣奸悽顖涘浮閹瑦绻濋崶銊у帾婵犵數鍊埀顒勫磻閹剧粯鐓?..");
    const resp = await window.authFetch("/api/presets");
    const data = await safeJson(resp);
    presetsOverview = data.presets || [];
    activePresetId = data.active ? data.active.preset_id : null;

    if (presetSelectEl) {
      presetSelectEl.innerHTML = "";
      for (const p of presetsOverview) {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.name + (p.is_default ? " (濠电姷鏁告慨鐢割敊閺嶎厼绐楁俊銈呭暞閺嗘粍淇婇妶鍛殶闁活厽鐟╅弻鐔兼倻濡晲绮堕梺閫炲苯澧剧紒鐘虫尭閻ｉ攱绺界粙璇俱劍銇勯弮鍥撴繛?" : "");
        presetSelectEl.appendChild(opt);
      }
      if (activePresetId) presetSelectEl.value = activePresetId;
    }

    // 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠Χ閸℃ぞ绮℃俊鐐€栭崝褏绮婚幋鐘差棜闁秆勵殕閻撴洘绻涢崱妤佺婵″弶妞介弻锝呪攽婵犲倻鍘繛锝呮搐閿曨亪銆佸☉妯锋斀闁规崘宕靛畷顏勨攽閻愯尙鎽犵紒顔肩灱缁辩偞绻濋崶褑鎽曢梺缁樻⒒閸樠呯不濮樿鲸鍠愮€广儱顦Ч鏌ュ级閸稑濡稿ù婊勭矒閺屾洟宕煎┑鍥ф闂侀潻绲界紞濠囧箺閸洘鍊烽柣鎴烆焽閸樺憡绻濋姀锝嗙【闁挎洩闄勭粋鎺楀鎺虫禍婊堢叓閸ラ鍒板褜鍨堕弻鏇㈠炊瑜嶉顓犫偓娈垮櫘閸ｏ綁宕洪埀顒併亜閹哄棗浜鹃柣鎾卞€濋弻锝夊籍閸屾艾浠樼紓浣哄У瀹€鎼佸蓟濞戙垹绠涢梻鍫熺⊕閻忓牏绱撴担鎻掍壕闁诲函缍嗛崑浣圭濠婂牊鐓欓柡澶婄仢椤ｆ娊鏌涢幒宥呭祮闁哄苯绉烽¨渚€鏌涢幘瀵告噮濠㈣娲熼、姗€鎮╅幇浣圭稐?
    const currentPreset = presetsOverview.find(p => p.id === activePresetId);
    const presetName = currentPreset ? (currentPreset.name + (currentPreset.is_default ? " (濠电姷鏁告慨鐢割敊閺嶎厼绐楁俊銈呭暞閺嗘粍淇婇妶鍛殶闁活厽鐟╅弻鐔兼倻濡晲绮堕梺閫炲苯澧剧紒鐘虫尭閻ｉ攱绺界粙璇俱劍銇勯弮鍥撴繛?" : "")) : activePresetId || "-";
    
    if (presetActiveHintEl) setText(presetActiveHintEl, "Active: " + presetName);
    if (presetStatusEl) setText(presetStatusEl, "就绪");
    if (presetStatusEl) setText(presetStatusEl, "就绪");
    const toLoad = (presetSelectEl && presetSelectEl.value) ? presetSelectEl.value : (presetsOverview[0] && presetsOverview[0].id);
    if (toLoad) await loadPresetDetail(toLoad);
  }

  async function loadPresetDetail(presetId) {
    if (!presetId) return;
    if (presetStatusEl) setText(presetStatusEl, "闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偛顦甸崹楣冨箛娴ｅ湱绋佺紓鍌氬€烽悞锕佹懌闂佸憡鐟ョ换姗€寮婚悢纰辨晬闁挎繂娲ｅЧ妤呮偡濠婂懎顣奸悽顖涘浮閹瑦绻濋崘锔跨盎濡炪倖鎸鹃崰搴ｇ箔瑜旈弻锝夘敇閻曚焦鐤佸┑顔硷攻濡炶棄鐣烽妸锔剧瘈闁告劦鐓堝Σ閬嶆⒒娓氣偓濞艰崵绱為崱娑橀棷闁挎繂鎳愰弳?..");
    const resp = await window.authFetch("/api/presets/" + encodeURIComponent(presetId));
    if (!resp.ok) {
      if (presetStatusEl) setText(presetStatusEl, "加载失败");
      return;
    }
    currentPreset = await resp.json();
    selectedNodeId = currentPreset && currentPreset.root ? currentPreset.root.id : null;
    
    // 闂傚倸鍊搁崐鎼佸磹閹间礁纾归柣鎴ｅГ閸婂潡鏌ㄩ弴姘舵濞存粌缍婇弻娑㈠箛閸忓摜鏁栭梺娲诲幗閹瑰洭寮诲☉銏╂晝闁挎繂妫涢ˇ銊╂⒑缁嬫鍎涘ù婊庝邯瀵鈽夐姀鐘靛姶闂佸憡鍔曟晶浠嬪礉閻戣姤鈷戠€规洖娲﹂崵鈧紓浣割槺閺佺粯淇婇悽绋跨妞ゆ牗姘ㄩ惈鍕⒑閹肩偛鍔撮柣蹇旂箞楠炴绱掑Ο鐓庡箰闂備胶纭跺褔寮插☉姗嗗殨妞ゆ洍鍋撻柡灞糕偓宕囨殕閻庯綆鍓欓崺宀勬煣娴兼瑧绉柡灞剧洴閳ワ箓骞嬪┑鍥╀壕闂備礁鎲￠敃鈺呭磻婵犲偆娼?
    presetModified = false;
    modifiedNodes.clear();
    updateSaveButtonState();
    
    renderTree();
    syncEditor();
    if (presetStatusEl) setText(presetStatusEl, "就绪");
    if (presetStatusEl) setText(presetStatusEl, "就绪");

  async function savePreset() {
    if (!currentPreset) return;
    if (presetStatusEl) setText(presetStatusEl, "濠电姷鏁告慨鐑藉极閹间礁纾块柟瀵稿Т缁躲倝鏌﹀Ο渚＆婵炲樊浜濋弲婊堟煟閹伴潧澧幖鏉戯躬濮婅櫣绮欑捄銊т紘闂佺顑囬崑銈呯暦閹达箑围濠㈣泛顑囬崢顏呯節閻㈤潧孝缂佺粯鍔欓妴鍛搭敆閸曨剛鍘?..");
    const resp = await window.authFetch("/api/presets/" + encodeURIComponent(currentPreset.id), {
      method: "PUT",
      body: JSON.stringify({
        id: currentPreset.id,
        name: currentPreset.name,
        version: currentPreset.version || 1,
        root: currentPreset.root,
        meta: currentPreset.meta || {}
      })
    });
    if (!resp.ok) {
      const t = await resp.text();
      throw new Error(t);
    }
    
    // 闂傚倸鍊搁崐鎼佸磹閹间礁纾归柣鎴ｅГ閸婂潡鏌ㄩ弴姘舵濞存粌缍婇弻娑㈠箛閸忓摜鏁栭梺娲诲幗閹瑰洭寮诲☉銏╂晝闁挎繂妫涢ˇ銊╂⒑缁嬫鍎涘ù婊庝邯瀵鈽夐姀鐘靛姶闂佸憡鍔曟晶浠嬪礉閻戣姤鈷戠€规洖娲﹂崵鈧紓浣割槺閺佺粯淇婇悽绋跨妞ゆ牗姘ㄩ惈鍕⒑閹肩偛鍔撮柣蹇旂箞楠炴绱掑Ο鐓庡箰闂備胶纭跺褔寮插☉姗嗗殨妞ゆ洍鍋撻柡灞糕偓宕囨殕閻庯綆鍓欓崺宀勬煣娴兼瑧绉柡灞剧洴閳ワ箓骞嬪┑鍥╀壕闂備礁鎲￠敃鈺呭磻婵犲偆娼?
    presetModified = false;
    modifiedNodes.clear();
    updateSaveButtonState();
    
    await loadPresetsOverview();
  }

  // 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗ù锝堟缁€濠傗攽閻樻彃浜為柣鎺旀櫕閹叉瓕绠涢弴鐕佹綗闂佺粯鍔曢顓犲姬閳ь剟姊洪幖鐐插妧闁搞儺鐓夌槐顒勬⒒閸屾瑨鍏岀紒顕呭灦瀹曞綊宕奸弴妞诲亾閿曞倸鐐婃い鎺嗗亾闁绘挻顭囬埀顒€绠嶉崕鍗炍涘☉姘К闁逞屽墴濮婂宕掑鍗烆杸缂備礁顑嗙敮陇妫㈤梺缁橆焽缁垶鎮″▎鎾寸厽闁挎繂鎳撶€氫即鏌嶇拠鑼ⅵ闁哄备鈧磭鏆嗛柍褜鍓熷畷浼村箻鐠囪尙鐛ユ繝鐢靛Т娴硷綁鎮㈤崨濠傤潯闂佸搫顦伴娆徫涘鍫熲拻闁稿本鑹鹃埀顒勵棑缁牊绗熼埀顒勭嵁閺嶎収鏁冮柨鏃囨娴滈亶姊虹化鏇炲⒉闁炬柨顑夊畷鍫曨敆婢跺娅旈梻渚€鈧偛鑻晶鎾煟濞戝崬娅嶇€规洖銈告俊鐑藉Ψ鎼存ɑ娅婇柡灞界У濞碱亪骞忕仦钘夊腐闂?
  async function saveAllChanges() {
    if (!currentPreset) return;
    
    // 婵犵數濮烽弫鍛婃叏閻戝鈧倿鎸婃竟鈺嬬秮瀹曘劑寮堕幋鐙呯幢闂備線鈧偛鑻晶鎾煛鐏炲墽銆掗柍褜鍓ㄧ紞鍡涘磻閸涱厾鏆︾€光偓閸曨剛鍘搁悗鍏夊亾閻庯綆鍓涢敍鐔哥箾鐎电顎撳┑鈥虫喘楠炲繘鎮╃拠鑼唽闂佸湱鍎ら崺鍫濐焽閵夈儮鏀介柣妯活問閺嗩垶鏌嶈閸撴瑩宕捄銊ф／鐟滄棃寮婚悢纰辨晩闁绘挸绨堕崑鎾诲箹娴ｇ懓浠奸梺缁樺灱濡嫬鏁梻浣稿暱閹碱偊宕愰悷鎵虫瀺闁糕剝绋掗埛鎴︽煕韫囨洖甯跺褜鍨堕弻娑㈠Ω閿曗偓閳绘洟鎸婂┑瀣厽婵°倐鍋撻柣妤€锕畷锝堢疀濞戞瑧鍘甸梺缁樺灦钃遍悘蹇曟暬閺屽秹顢涘☉娆戭槰闂侀潧娲ょ€氫即銆佸鈧幃娆撴濞戞帒寰嶅┑锛勫亼閸婃垿宕瑰ú顏佲偓锕傚炊閳哄偆娼熼梺鍦劋閸╁牆顭囬妸鈺傜厱妞ゆ劗濮撮悘顕€鏌ｉ幘鏉戠伌婵﹦绮幏鍛村川婵犲倹娈樻繝鐢靛仩椤曟粎绮婚幘宕囨殾闁瑰墎鐡旈弫瀣煃瑜滈崜娆撴偩?
    const presetInfo = presetsOverview.find(p => p.id === currentPreset.id);
    if (presetInfo && presetInfo.is_default) {
      alert("默认预设不可修改，请先复制或创建新预设。");
      return;
    }
    
    if (!presetModified) {
      alert("当前没有可保存的预设改动。");
      return;
    }
    
    try {
      await savePreset();
      if (presetStatusEl) setText(presetStatusEl, "已保存");
      
      // 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠Χ閸屾矮澹曞┑顔筋焽閸樠勬櫠椤栫偞鐓涢柛娑欐緲閻撴劗绱掗崒娑樼闁逞屽墾缂嶅棝鍩€椤掑寮块梻鍕楠炲牓濡搁妷顔藉缓闂佺硶鍓濋〃鍛不婵犳碍鈷戠€规洖娲﹂崵鈧紓浣割槺閺佹悂骞戦姀鐘斀閻庯綆鍋掑Λ鍐ㄢ攽閻愭潙鐏﹂柣鐕佸灠铻為柕鍫濐槹閳锋垿鏌涢敂璇插箺婵炲懏娲栭埞鎴︽倷閳轰椒澹曢梻鍌欑閹碱偊鎯夋總绋跨獥闁规崘顕ч悞鍨亜閹哄秷鍏岄柍顖涙礋閺屻劌顫濋鑺ユ杸濡炪倖鏌ㄩ崥瀣箹閹扮増鐓冮悷娆忓閻忓瓨銇勯姀锛勬噰闁诡喖澧芥禒锕傚箚瑜嶉悘锟犳⒒閸屾瑦绁版い鏇熺墵瀹曡瀵奸弶鎴犳焾闂佸搫顦伴崹褰掑汲閿曞倹鐓熼柡鍐ㄥ€甸幏锟犳煛娴ｅ憡顥㈤柡灞界Х椤т線鏌涢幘瀵糕槈妞ゆ洏鍎茬换婵嬪炊瑜庡畵宥咁渻閵堝棙灏靛┑顔惧厴閺佸秴顭ㄩ崼鐔叉嫼?
      setTimeout(() => {
        if (presetStatusEl) setText(presetStatusEl, "就绪");
      }, 2000);
      
    } catch (error) {
      console.error("濠电姷鏁告慨鐑藉极閹间礁纾块柟瀵稿Т缁躲倝鏌﹀Ο渚＆婵炲樊浜濋弲婊堟煟閹伴潧澧幖鏉戯躬濮婅櫣绮欑捄銊т紘闂佺顑囬崑銈呯暦閹达箑围濠㈣泛顑囬崢顏呯節閻㈤潧孝缂佺粯甯￠幃鐐綇閳哄啰锛滈梺鍛婃尫缁€浣圭鏉堚斁鍋撳▓鍨灈闁绘牜鍘ч悾閿嬬附閸撳弶鏅濆銈庡亽閸樺ジ宕甸柆宥嗙厽?", error);
      if (presetStatusEl) setText(presetStatusEl, "濠电姷鏁告慨鐑藉极閹间礁纾块柟瀵稿Т缁躲倝鏌﹀Ο渚＆婵炲樊浜濋弲婊堟煟閹伴潧澧幖鏉戯躬濮婅櫣绮欑捄銊т紘闂佺顑囬崑銈呯暦閹达箑围濠㈣泛顑囬崢顏呯節閻㈤潧孝缂佺粯甯￠幃鐐綇閳哄啰锛滈梺鍛婃尫缁€浣圭鏉堚斁鍋撳▓鍨灈闁绘牜鍘ч悾閿嬬附閸撳弶鏅濆銈庡亽閸樺ジ宕甸柆宥嗙厽? " + error.message);
    }
  }

  window.savePresetChanges = saveAllChanges;

  window.saveCurrentPreset = async function() {
    if (!currentPreset) return;
    const presetInfo = presetsOverview.find(p => p.id === currentPreset.id);
    if (presetInfo && presetInfo.is_default) {
      return;
    }
    await savePreset();
  };

  async function createPreset() {
    const name = prompt("New preset name:", "New preset");
    if (!name) return;
    if (presetStatusEl) setText(presetStatusEl, "闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偛顦甸弫宥夊礋椤掍焦顔囨繝寰锋澘鈧洟宕导瀛樺剹婵炲棙鎸婚悡娆撴倵閻㈡鐒鹃崯鍝ョ磼閹冪稏缂侇喗鐟╁濠氭偄閻撳海鐣鹃悷婊勭矒瀹曠敻鎮㈤崗鑲╁帗?..");
    const resp = await window.authFetch("/api/presets?name=" + encodeURIComponent(name), { method: "POST" });
    if (!resp.ok) {
      if (presetStatusEl) setText(presetStatusEl, "Create failed");
      return;
    }
    const p = await resp.json();
    if (presetStatusEl) setText(presetStatusEl, "Created");
    await loadPresetsOverview();
    if (presetSelectEl) presetSelectEl.value = p.id;
    await loadPresetDetail(p.id);
  }

  async function setActivePreset() {
    if (!presetSelectEl) return;
    const pid = presetSelectEl.value;
    if (!pid) return;
    const resp = await window.authFetch("/api/presets/active", {
      method: "PUT",
      body: JSON.stringify({ preset_id: pid })
    });
    if (!resp.ok) {
      const t = await resp.text();
      if (presetStatusEl) setText(presetStatusEl, "设为当前失败：" + t);
      return;
    }
    const data = await resp.json();
    activePresetId = data.preset_id;
    
    // 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠Χ閸℃ぞ绮℃俊鐐€栭崝褏绮婚幋鐘差棜闁秆勵殕閻撴洘绻涢崱妤佺婵″弶妞介弻锝呪攽婵犲倻鍘繛锝呮搐閿曨亪銆佸☉妯锋斀闁规崘宕靛畷顏勨攽閻愯尙鎽犵紒顔肩灱缁辩偞绻濋崶褑鎽曢梺缁樻⒒閸樠呯不濮樿鲸鍠愮€广儱顦Ч鏌ュ级閸稑濡稿ù婊勭矒閺屾洟宕煎┑鍥ф闂侀潻绲界紞濠囧箺閸洘鍊烽柣鎴烆焽閸樺憡绻濋姀锝嗙【闁挎洩闄勭粋鎺楀鎺虫禍婊堢叓閸ラ鍒板褜鍨堕弻鏇㈠炊瑜嶉顓犫偓娈垮櫘閸ｏ綁宕洪埀顒併亜閹哄棗浜鹃柣鎾卞€濋弻锝夊籍閸屾艾浠樼紓浣哄У瀹€鎼佸蓟濞戙垹绠涢梻鍫熺⊕閻忓牏绱撴担鎻掍壕闁诲函缍嗛崑浣圭濠婂牊鐓欓柡澶婄仢椤ｆ娊鏌涢幒宥呭祮闁哄苯绉烽¨渚€鏌涢幘瀵告噮濠㈣娲熼、姗€鎮╅幇浣圭稐?
    const currentPreset = presetsOverview.find(p => p.id === activePresetId);
    const presetName = currentPreset ? (currentPreset.name + (currentPreset.is_default || data.is_default ? " (濠电姷鏁告慨鐢割敊閺嶎厼绐楁俊銈呭暞閺嗘粍淇婇妶鍛殶闁活厽鐟╅弻鐔兼倻濡晲绮堕梺閫炲苯澧剧紒鐘虫尭閻ｉ攱绺界粙璇俱劍銇勯弮鍥撴繛?" : "")) : activePresetId || "-";
    
    if (presetActiveHintEl) setText(presetActiveHintEl, "Active: " + presetName);
    if (presetStatusEl) setText(presetStatusEl, "Active preset updated");
    
    // 缂傚倸鍊搁崐鎼佸磹閻戣姤鍤勯柛顐ｆ礃閹偤骞栧ǎ顒€濡奸柣顓燁殜楠炴牕菐椤掆偓婵¤偐绱掗幇顓ф疁闁哄矉绻濆畷鍫曞煛娴ｅ浄绲块埀顒冾潐濞叉牕顕ｉ崼鏇炵疄闁靛鍎哄銊╂煕閳╁喚娈旂紒鐘差煼濮婂搫鐣烽崶鈺佺濠碘槅鍋勯崯鎾嵁閸愩剮鏃堝川椤旇姤鐝抽梺纭呭亹鐞涖儵鍩€椤掑啫鐨洪柣鈺佸娣囧﹪鎮欓鍕ㄥ亾閺囩姭鍋撳☉鎺撴珚闁诡喚鍏橀崺鈩冪瑹閸ャ劎绋佹繝鐢靛仜濡﹥绂嶉崼鏇炴瀬闁告劦鍠楅悡蹇涚叓閸パ嶆敾婵炲懎妫濆顐﹀醇閵夛腹鎷洪柣鐘叉处瑜板啴顢楅姀銈嗙厱婵犻潧妫濋崣鍕偓瑙勬礃缁诲倿鎮惧┑瀣闁宠鍎虫禍楣冩煕濞戝崬鏋ら梻鍕缁辨帞鈧綆浜炴禒銏ゆ煠閺夎法浠㈤柍瑙勫灴閹瑩宕ｆ径妯伙紒闂備礁鎲″褰掋€冩繝鍌ゅ殨闁规儼濮ら崑鎰磽娴ｉ姘跺箯缂佹绠鹃柟鍓ь棎婢规ɑ绻涚仦鍌氣偓鏍矉瀹ュ拋鐓ラ柛鏇楁櫃缁ㄥ姊洪幐搴㈩梿妞ゆ泦鍐ｆ瀺鐎广儱顦伴悡娆撴煣韫囷絽浜為柟鍐叉处椤ㄣ儵鎮欏顔煎壎闂佽桨绀侀崐鍧楀箰婵犲啫绶炲璺侯儑濞兼牠姊婚崒姘偓鐑芥嚄閸洖鍌ㄧ憸鏃堢嵁濡も偓椤劑宕煎☉鎺戜壕闁稿本绋撻々鐑芥倵閿濆簼绨介柨娑欑洴濮婅櫣鎲撮崟顐㈠Б闂佸鏉垮闁告帒锕獮姗€顢欓挊澶夊寲闂備焦鎮堕崕鑽ゅ緤濞差亜纾婚柟鎹愵嚙缁€鍐煕濞嗗繐鈧綊銆冮崼銏☆潟?
    if (presetSelectEl.value !== activePresetId) {
      presetSelectEl.value = activePresetId;
    }
  }

  async function deletePreset() {
    if (!presetSelectEl) return;
    const pid = presetSelectEl.value;
    if (!pid) return;
    
    const presetToDelete = presetsOverview.find(p => p.id === pid);
    if (presetToDelete && presetToDelete.is_default) {
      alert("Default preset cannot be deleted.");
      return;
    }
    
    if (!confirm("确认删除这个预设吗？")) return;

    if (presetStatusEl) setText(presetStatusEl, "正在删除预设...");
    const resp = await window.authFetch("/api/presets/" + encodeURIComponent(pid), { method: "DELETE" });
    if (!resp.ok) {
      const t = await resp.text();
      if (presetStatusEl) setText(presetStatusEl, "删除失败：" + t);
      if (presetStatusEl) setText(presetStatusEl, "删除失败：" + t);
    }
    if (presetStatusEl) setText(presetStatusEl, "已删除");
    await loadPresetsOverview();
  }

  async function importPreset() {
    console.log("Import preset triggered");
    const f = presetImportFileEl && presetImportFileEl.files ? presetImportFileEl.files[0] : null;
    console.log("闂傚倸鍊搁崐鎼佸磹閹间礁纾瑰瀣椤愪粙鏌ㄩ悢鍝勑㈢痪鎯ь煼閺屾盯寮撮妸銉р偓顒勬煕閵夘喖澧紒鐘劜閵囧嫰寮崒娑樻畬婵炲瓨绮庨崑鎾诲箞閵娿儙鐔虹矙閸喖顫撳┑鐘愁問閸犳牠宕愰崸妤€钃熼柣鏃傗拡閺佸秵鎱ㄥ鍡楀婵炲牆顭烽幃妤冩喆閸曨剛顦梺鍝ュУ閻楃娀濡存担鑲濇梹鎷呴悷閭︹偓鎾绘煟閻愬鈻撻柍褜鍓欓崢鏍ㄧ珶閺囩儐娓婚柕鍫濇閳锋劗绱?", f);
    
    if (!f) {
      alert("请选择要导入的 JSON 文件。");
      return;
    }
    
    if (presetStatusEl) setText(presetStatusEl, "正在导入预设...");
    
    try {
      const text = await f.text();
      console.log("闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈡晝閳ь剛澹曢崷顓犵＜閻庯綆鍋撶槐鈺傜箾瀹割喕绨奸柡鍛叀閺屾稑鈽夐崣妯煎嚬闂佽楠搁…宄邦潖濞差亝顥堟繛鎴炴皑閻ゅ嫰姊虹粙鍖℃敾婵炲弶绮庨崚鎺楀醇閵夈儳顦ㄥ銈嗘⒒閺咁偊宕㈤崡鐐╂斀闁绘劖娼欓悘銉р偓瑙勬处閸撴瑩顢氶敐鍡愬亝闁告劏鏅濋崢閬嶆⒑缂佹ɑ顥堥柡鈧柆宥呯獥婵☆垳绮崣蹇撯攽閻樻彃浜為柣鎾炽偢閺屾盯鍩為幆褌澹曞┑锛勫亼閸婃牜鏁幒鏂哄亾濮樼厧澧寸€规洖缍婂畷鎺戔槈閺嶏妇鐩庨梻浣告惈閸燁偊宕愰悽绋跨闁跨喓濮甸悡?", text.length);
      
      let payload;
      try { 
        payload = JSON.parse(text); 
        console.log("JSON validation passed");
      } catch (e) { 
        console.error("JSON闂傚倸鍊搁崐宄懊归崶褏鏆﹂柣銏㈩焾缁愭鏌熼幍顔碱暭闁稿绻濆鍫曞醇濮橆厽鐝旂紓浣界堪閸婃洝鐏冮梺鎸庣箓閹冲酣寮抽悙鐑樼厱濠电姴瀚弳顒勬煛鐏炶鈧繈鐛笟鈧獮鎺楀箣濠靛棭娼涚紓鍌氬€风粈浣规櫠鎼淬劌纾婚柕鍫濇媼閸ゆ洟鏌涢锝嗙闂佸崬娲﹂妵鍕箛閸偆绐旈梺鍛婂灣缁瑩骞?", e);
        alert("JSON 解析失败。"); 
        return; 
      }

      const nameHint = prompt("Preset name:", f.name.replace(/\.json$/i, ""));
      if (!nameHint) {
        if (presetStatusEl) setText(presetStatusEl, "Import cancelled");
        return;
      }

      console.log("Importing preset via API");
      const resp = await window.authFetch("/api/presets/import", {
        method: "POST",
        body: JSON.stringify({ payload, name_hint: nameHint })
      });
      
      console.log("API闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偛顦甸弫宥夊礋椤掆偓鎼村﹪姊虹粙鎸庢拱缂侇喖閰ｉ幆宀勫箻缂佹ê鈧敻鏌涢…鎴濅簽闁硅棄鍟埞鎴︻敊閽樺鏋欓梺鍝勭焿缁辨洘绂掗敂鐐珰闁圭粯甯掗～姘舵⒒娴ｄ警鐒炬い鎴濇瀹曟繂鈻庨幘瀹犳憰闂侀潧鐗嗛ˇ顖涘閻樼粯鐓忓鑸得弸鐔告叏閿濆懐鐒告慨?", resp.status);
      
      if (!resp.ok) {
        const t = await resp.text();
        console.error("闂傚倸鍊搁崐宄懊归崶顒夋晪鐟滃秹婀侀梺缁樺灱濡嫰寮告笟鈧弻鐔兼⒒鐎靛壊妲梺绋胯閸斿酣骞夐幖浣告閻犳亽鍔嶅▓楣冩⒑閹稿海绠撴い锔诲灦閻涱噣濮€閳ヨ尙绠氬銈嗙墬缁诲啴顢旈悩鐢电＜闁归偊鍠栨禒閬嶆煛鐏炵澧茬€垫澘瀚换婵嬪礋椤愮喐瀚涢梻鍌欒兌椤牓顢栭崨姝ゅ洭骞庨柧?", t);
        if (presetStatusEl) setText(presetStatusEl, "Import failed: " + t);
        return;
      }
      
      const p = await resp.json();
      console.log("闂傚倸鍊搁崐宄懊归崶顒夋晪鐟滃秹婀侀梺缁樺灱濡嫰寮告笟鈧弻鐔兼⒒鐎靛壊妲梺绋胯閸斿酣骞夐幖浣告閻犳亽鍔嶅▓楣冩⒑閹稿海绠撴い锔诲灦閻涱噣濮€閿涘嫮顔曢梺鐟邦嚟閸庢劙鎮為懞銉ｄ簻闁规儳鐡ㄩ妵婵囨叏婵犲洨绱伴柕鍥ㄥ姍楠炴帡骞嬪鍐╃€抽梻鍌欑閹诧繝骞愭繝姘仭闁冲搫鎳忛弲?", p.id);
      
      if (presetStatusEl) setText(presetStatusEl, "Imported");
      await loadPresetsOverview();
      if (presetSelectEl) presetSelectEl.value = p.id;
      await loadPresetDetail(p.id);
      
    } catch (error) {
      console.error("闂傚倸鍊搁崐宄懊归崶顒夋晪鐟滃秹婀侀梺缁樺灱濡嫰寮告笟鈧弻鐔兼⒒鐎靛壊妲梺绋胯閸斿酣骞夐幖浣告閻犳亽鍔嶅▓楣冩⒑閹稿海绠撴い锔诲灦閻涱噣濮€閳ヨ尙绠氬銈嗙墬缁诲秹宕悜妯诲弿婵鐗忛悾鍨叏婵犲啯銇濇鐐寸墵閹瑩骞撻幒鎴綍闂傚倷绀侀幖顐﹀磹妞嬪孩顐芥慨姗嗗墻閸ゆ洖鈹戦悩瀹犲閸ユ挳姊洪崨濠佺繁濞存粍绻堥敐鐐差吋婢跺鎷洪梺鑽ゅ枑婢瑰棙绂掗姀銈嗙厱闁绘洑绀佹禍浼存煟濞戝崬娅嶇€殿喕绮欓、姗€鎮㈤崫鍕疄闂傚倷绶氬褔鎮ч崱姗嗘缂佸顑欓崵鏇熴亜閺囨浜鹃梺?", error);
      if (presetStatusEl) setText(presetStatusEl, "Import skipped");
    }
    
    if (presetImportFileEl) presetImportFileEl.value = "";
  }

  async function renamePreset() {
    if (!presetSelectEl) return;
    const pid = presetSelectEl.value;
    if (!pid) return;
    
    const currentPresetInfo = presetsOverview.find(p => p.id === pid);
    if (currentPresetInfo && currentPresetInfo.is_default) {
      alert("默认预设不能重命名。");
      return;
    }
    
    const newName = prompt("重命名预设：", currentPreset ? currentPreset.name : "");
    if (!newName || newName.trim() === "") return;
    
    if (presetStatusEl) setText(presetStatusEl, "闂傚倸鍊搁崐鎼佸磹閹间礁纾归柣鎴ｅГ閸婂潡鏌ㄩ弴姘舵濞存粌缍婇弻娑㈠箛閸忓摜鏁栭梺娲诲幗閹瑰洭寮婚悢铏圭＜闁靛繒濮甸悘鍫㈢磽娴ｅ搫啸濠电偐鍋撻梺鍝勮閸旀垿骞冮姀銈呬紶闁告洘鍨崹浠嬪箖瀹勬壋鏋庢繛鍡楁禋濞差參姊洪柅鐐茶嫰婢ь喚绱掗悩鑼х€规洘娲樺蹇涘煘閹傚濠殿喗顭囬崢褔鎮橀敂閿亾?..");
    
    currentPreset.name = newName.trim();
    const resp = await window.authFetch("/api/presets/" + encodeURIComponent(pid), {
      method: "PUT",
      body: JSON.stringify({
        id: currentPreset.id,
        name: currentPreset.name,
        version: currentPreset.version || 1,
        root: currentPreset.root,
        meta: currentPreset.meta || {}
      })
    });
    
    if (!resp.ok) {
      const t = await resp.text();
      if (presetStatusEl) setText(presetStatusEl, "Rename failed: " + t);
      return;
    }
    
    if (presetStatusEl) setText(presetStatusEl, "Renamed");
    await loadPresetsOverview();
  }

  async function exportPreset() {
    if (!currentPreset) return;
    const resp = await window.authFetch("/api/presets/export/" + encodeURIComponent(currentPreset.id));
    if (!resp.ok) {
      // 濠电姷鏁告慨鐑藉极閸涘﹥鍙忛柣鎴濐潟閳ь剙鍊圭粋鎺斺偓锝庝簽閸旓箑顪冮妶鍡楀潑闁稿鎹囬弻娑㈡偄闁垮浠撮梺绯曟杹閸嬫挸顪冮妶鍡楀潑闁稿鎸剧槐鎾愁吋閸滃啳鍚Δ鐘靛仜閸燁偉鐏掗柣鐘叉穿鐏忔瑧绮ｉ悙鐑樷拺鐟滅増甯掓禍浼存煕閹惧绠氭い銈呭€垮缁樻媴娓氼垱鏁繝銏㈡嚀閻楁捇鐛幘娲绘晜闁糕剝鐟чˇ顖炴⒑缁洖澧查柨姘亜閺囶澀鎲鹃柡灞剧〒娴狅箓宕滆閳ь剚甯炵槐鎺楁偐閼姐倗鏆梺璇″枟閿曘垽骞冨▎鎾村仺闁绘劕鍘滈崑鎾寸節閸ャ劎鍘遍柣搴秵閸嬪懐浜搁銏＄厽闁挎繂娲ら崢瀵糕偓瑙勬礀閻栧吋淇婇幖浣规櫆濡わ絽鍟€氫粙姊?export 闂傚倸鍊搁崐鎼佸磹瀹勬噴褰掑炊椤掑﹦绋忔繝銏ｆ硾椤戝洭銆呴幓鎹楀綊鎮╁顔煎壈缂佺偓鍎冲鈥愁嚕閸洖閱囨い鎰垫線缁ㄥ瓨绻涚€涙鐭庢い顐㈩槺閹广垹鈽夐姀鐘殿吅濠电偛妫楃换鎺撶妤ｅ啯鈷戦柛婵嗗婵ジ鏌涢幘璺烘灈妤犵偛鍟～婊堝焵椤掑嫬绠栨繛鍡樻尰閸ゅ绻涢崼鐔奉嚋妞ゃ儱顦靛娲嚒閵堝憛锟犳煟閹虹偟鐣抽柕鍥ㄥ姍瀹曟﹢顢欓悾宀€鏆㈤梻鍌氬€烽懗鍓佸垝椤栫偞鏅濋柍鍝勬噹缁愭鏌″搴″箹缂佲偓婢舵劖鐓忛柛顐ｇ箖椤ョ姷绱掗悩鑽ょ暫闁哄瞼鍠撶槐鎺懳熼搹鍦嚃闂備胶顭堥鍐磿閺屻儯鈧啴濡烽埡鍌氣偓鐑芥煛婢跺鐏﹂悹鍥╁仦缁绘繄鍠婃径宀€锛熼梺绋跨箲钃卞ǎ鍥э躬閹粎绮电€ｎ偅娅撻梻浣侯焾缁绘帡鍩涢崼銉ョ柈鐎光偓閸曨兘鎷?currentPreset
      const blob = new Blob([JSON.stringify(currentPreset, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = (currentPreset.name || "preset") + ".json";
      a.click();
      URL.revokeObjectURL(a.href);
      return;
    }
    const data = await resp.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = (data.name || "preset") + ".json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // 缂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾惧綊鏌ｉ幋锝呅撻柛濠傛健閺屻劑寮撮悙娴嬪亾閹间礁鍨傞柛宀€鍋為悡鐔兼煏韫囨洖校闁哥喓鍋ら弻娑氣偓锛卞嫭鐝氶梺鍝勭焿缂嶄線鐛崶顒侇棃婵炴垶锕╁鐐繆閻愵亜鈧劙寮插鍫熷亗闁跨喓濮寸粻鏍ㄤ繆閵堝懏鍣洪柡鍛叀閺屾稓浠﹂崜褉濮囬梺缁樼箖濞叉牠鈥?
  if (presetSelectEl) {
    presetSelectEl.addEventListener("change", async () => {
      await loadPresetDetail(presetSelectEl.value);
    });
  }
  // 濠电姷鏁告慨鐑藉极閹间礁纾块柟瀵稿Т缁躲倝鏌﹀Ο渚＆鐟滅増甯掔壕濂告煟閹邦垰鐨洪柣娑栧劦濮婃椽宕崟顓涙瀱闂佸憡蓱濡啫鐣烽崼鏇ㄦ晢闁逞屽墴閹苯螖閳ь剟鈥﹂崸妤佸殝闁汇垻鍋ｉ埀顒佸浮閺岋綁顢橀悤浣圭杹濠殿喖锕ュ钘夌暦閵婏妇绡€闁告劦鐓堝Σ閬嶆⒒娓氣偓濞艰崵绱為崱娑橀棷闁挎繂鎳愰弳锔姐亜閺嶃劎鈯曢柛搴ｅ枛閺屾洘绻濊箛鏇犳殸闂侀€炲苯澧伴柡浣割煼瀵鏁愭径濠庢綂闂侀潧鐗嗗Λ娆撴煥椤撱垺鐓熼柕蹇婃櫅閻忕娀鏌ｉ弽褋鍋㈢€殿喛顕ч埥澶娢熼柨瀣偓濠氭椤愩垺澶勬俊顐㈢箰铻為柨鏇楀亾閾绘牠鏌ｅ鈧褎绂掗敃鍌涚厱闁哄啠鍋撻柣妤佹礋椤㈡岸濡烽埡浣侯槹濡炪倖鐗楀銊╂偪閳ь剚淇婇悙顏勨偓鏍箰妤ｅ啫纾绘繛鎴欏灩缂佲晜銇勯幘璺轰汗闁衡偓娴犲鐓熼柟閭﹀灠閻ㄦ椽鏌熼悾灞叫ョ紒杈ㄥ浮椤㈡瑩鎳栭埡鍐ㄥП婵＄偑鍊戦崹娲偋閻樿尙鏆﹂柣鏃傗拡閺佸啴鏌ｉ弬鎸庢喐闁逞屽墮椤嘲顫忓ú顏咁棃婵炴垶姘ㄩ悿鍕⒑閹肩偛濮€鐎规洖鐏氱粩鐔煎即閻旀椽妾梺鍛婄☉閿曪箓宕㈤悽鍛婄厽閹兼番鍨婚埊鏇熴亜椤撶偞宸濈紒顔款嚙椤粓鍩€椤掑嫬钃?
  if (presetImportFileEl) {
    console.log("Loading preset tree into editor");
    presetImportFileEl.addEventListener("change", importPreset);
    
    // 婵犵數濮烽弫鍛婃叏閻戣棄鏋侀柟闂寸绾惧潡鏌熺€电啸缂佲偓婵犲洦鐓冪憸婊堝礈濮樿泛桅闁告洦鍨伴崡鎶芥煕閳╁喚娈旀い蹇ｄ邯閺屾稑鈻庤箛鏇狀啋闂佸搫鐭夌紞渚€鐛崶顒夋晢闁稿本鐟фす鎶芥⒑鐠囨彃顒㈤柛鎴濈秺瀹曟粓鎮㈤悡搴ゆ憰濠电偞鍨崹鍦不濞戙垺鈷掗柛顐ゅ枔閳藉绱掗悩渚殭闁宠鍨垮閬嶆倶韫囨梻鎳囬柍銉畵瀹曞ジ鏁愰崨顖氣偓鎺楁⒒閸屾瑧鍔嶉柟顔肩埣瀹曟洟鎳￠妶鍛瓘闂佸吋浜介崕鎻掆枍閻樼粯鐓欑紓浣姑涵鈧?
    presetImportFileEl.addEventListener("click", function() {
      console.log("Preset tree loaded");
    });
  } else {
    console.error("Failed to load preset tree:", err);
  }
  
  presetCreateBtn && presetCreateBtn.addEventListener("click", createPreset);
  presetSetActiveBtn && presetSetActiveBtn.addEventListener("click", setActivePreset);
  presetRenameBtn && presetRenameBtn.addEventListener("click", renamePreset);
  presetDeleteBtn && presetDeleteBtn.addEventListener("click", deletePreset);
  presetExportBtn && presetExportBtn.addEventListener("click", exportPreset);

  addGroupBtn && addGroupBtn.addEventListener("click", () => addChildNode("group"));
  addPromptBtn && addPromptBtn.addEventListener("click", () => addChildNode("prompt"));
  deleteNodeBtn && deleteNodeBtn.addEventListener("click", deleteSelectedNode);
  bindPresetEditorEvents();

  // =========================================================
  // B) API闂傚倸鍊搁崐鎼佸磹閹间礁纾归柣鎴ｅГ閸婂潡鏌ㄩ弴妤€浜惧銈庡幖閻忔繆鐏掗梺鍏肩ゴ閺呮繈鎮＄€ｎ喗鈷戦柛鎾村絻娴滄繃绻涢崣澶涜€跨€规洘鍨块、鏃堝醇閻斿搫骞堥梻浣规灱閺呮盯宕导鏉戠厐闁哄洢鍨洪悡娑㈡煕濠娾偓缁€浣规櫠閹绢喗鐓涢悘鐐插⒔濞叉挳鏌℃担绋库偓鍧楃嵁閸℃凹妲煎銈嗘尵缁椻偓 Config闂?
  // =========================================================
  const llmListEl = $("llm-config-list");
  const llmActiveHintEl = $("llm-active-hint");
  const llmStatusEl = $("llm-status");

  const llmNewBtn = $("llm-new-btn");
  const llmSetActiveBtn = $("llm-set-active-btn");
  const llmSaveBtn = $("llm-save-btn");
  const llmDeleteBtn = $("llm-delete-btn");

  const llmNameEl = $("llm-name");
  const llmBaseUrlEl = $("llm-base-url");
  const llmApiKeyEl = $("llm-api-key");
  const llmStreamEl = $("llm-stream");
  const llmModelSelectEl = $("llm-model-select");
  const llmRefreshModelsBtn = $("llm-refresh-models-btn");
  const llmDefaultModelEl = $("llm-default-model");

  let llmConfigs = [];
  let llmActive = { config_id: null, model: null };
  let selectedConfigId = null;

  function renderLLMList() {
    if (!llmListEl) return;
    llmListEl.innerHTML = "";
    for (const cfg of llmConfigs) {
      const row = document.createElement("div");
      row.className = "list-item" + (cfg.id === selectedConfigId ? " active" : "");
      row.style.display = "flex";
      row.style.alignItems = "center";
      row.style.gap = "10px";

      const left = document.createElement("div");
      left.style.flex = "1";
      const name = document.createElement("div");
      name.textContent = cfg.name || cfg.id;
      const sub = document.createElement("div");
      sub.className = "small-text muted";
      sub.textContent = (cfg.base_url || "") + (cfg.stream ? " 闂?stream" : " 闂?non-stream");
      left.appendChild(name);
      left.appendChild(sub);

      const badge = document.createElement("div");
      badge.className = "small-text";
      if (llmActive && llmActive.config_id === cfg.id) {
        badge.textContent = "Active";
      } else {
        badge.textContent = "";
      }

      row.appendChild(left);
      row.appendChild(badge);

      row.addEventListener("click", () => {
        selectedConfigId = cfg.id;
        fillLLMEditor(cfg);
        renderLLMList();
      });

      llmListEl.appendChild(row);
    }
    if (llmActiveHintEl) setText(llmActiveHintEl, "Active: " + (llmActive && llmActive.config_id ? llmActive.config_id : "-") + (llmActive && llmActive.model ? (" / " + llmActive.model) : ""));
  }

  function getSelectedCfg() {
    if (!selectedConfigId) return null;
    return llmConfigs.find(c => c.id === selectedConfigId) || null;
  }

  function fillLLMEditor(cfg) {
    if (!cfg) return;
    llmNameEl && (llmNameEl.value = cfg.name || "");
    llmBaseUrlEl && (llmBaseUrlEl.value = cfg.base_url || "");
    llmApiKeyEl && (llmApiKeyEl.value = cfg.api_key || "");
    llmStreamEl && (llmStreamEl.checked = cfg.stream !== false);
    llmDefaultModelEl && (llmDefaultModelEl.value = cfg.default_model || "");
  }

  function collectLLMEditor() {
    const selectedCfg = getSelectedCfg();
    // 闂傚倸鍊搁崐椋庣矆娓氣偓楠炴牠顢曚綅閸ヮ剦鏁冮柨鏇楀亾闁汇倗鍋撶换婵囩節閸屾粌顣洪梺钘夊暟閸犳牠寮婚弴鐔虹闁割煈鍠栨竟鍕攽閻愬弶鈻曞ù婊勭矒瀹曟﹢鍩€椤掆偓椤啴濡堕崱妯烘殫闂佺顑囬崑銈堟＂濠电娀娼ч鍡涘煕閹达附鐓曟繝闈涙椤忓瓨淇婇懠棰濇綈闁靛洤瀚伴獮瀣倷閸偄娅氶柣搴ゎ潐濞叉粓寮繝姘畺闁冲搫鍟扮壕鍏间繆椤栨繃銆冮柛鏍ㄧ墵濮婄粯鎷呴搹鐟扮闂佸憡鏌ㄧ换妯侯嚕閹绘帩鐓ラ柛顐墰缁嬪繑绻濋姀锝嗙【闁活剝鍋愭竟鏇熺附缁嬭法楠囬梺鍓插亝缁嬫垶淇婄捄銊х＜闁绘ê纾晶杈╃磼鏉堛劌绗ч柍褜鍓ㄧ紞鍡樼鐠轰綍锝夊川婵炲じ绨婚梺鐟板⒔閸嬨劑宕戦姀鈶╁亾鐟欏嫭绀堥柛鐘崇墵閵嗕礁螖閸涱厾鍔﹀銈嗗坊閸嬫挻銇勯弴顏嗙М鐎规洜顭堣灃濞达絽寮剁€氬ジ姊洪懡銈呬沪缂佸鐗撻崺鈧い鎺嗗亾闁告ɑ鐗楃粩?llmConfigs 闂傚倸鍊搁崐鎼佸磹瀹勬噴褰掑炊瑜滃ù鏍煏婵炵偓娅嗛柛濠傛健閺屻劑寮崒娑欑彧闂佺粯绻傞悥濂稿蓟濞戙垹鐒洪柛鎰典簼閸Ｑ囨⒑閹肩偛濡界紒璇插閸┾偓妞ゆ巻鍋撶紒鐘茬Ч瀹曟洟宕￠悙宥嗙☉閳藉濮€閻橀潧骞掗梻浣告惈閸熺娀宕戦幘缁樼厪闁搞儜鍐句純濡ょ姷鍋為…鍥箲閸曨垱鍎庨柟铏瑰仧缁夘噣鏌″畝瀣М闁轰焦鍔栧鍕緞鐎ｎ亝鐏撻梻鍌欑閹碱偊寮甸鍌滅煓闁硅揪绲挎禍浠嬫⒒娴ｈ櫣甯涢柟绋挎憸閳ь剚绋堥弲鐘诲箖濡ゅ啯瀚氱€瑰壊鍠楃€靛矂姊洪棃娑氬婵☆偅鐟﹀鍕礋椤栨稓鍘遍梺缁樏崯鍧楀传閻戞﹩娈?
    // 闂傚倸鍊搁崐椋庣矆娓氣偓楠炴牠顢曚綅閸ヮ剦鏁冮柨鏇楀亾闁汇倗鍋撶换婵囩節閸屾粌顤€闂佺顑戠换婵嬪蓟閵娾晛鍗抽柣鎰ゴ閸嬫捁銇愰幒鎴狅紱闁诲函缍嗛崰妤呭煕閹寸偑浜滈柟鍝勬娴滃墽绱撴担鍓叉Ц妞ゆ洦鍘鹃崚鎺楀醇閵夈儱鑰垮┑鐐村灦閻熝囧储椤忓牊鈷戦柛鎾村絻娴滄繄绱掔拠鎻掓殻閽樼喖鏌ｉ幇顔煎妺闁?isNewConfig 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈡晝閳ь剟鎮块鈧弻鐔煎箚閻楀牜妫勯梺鍝勫閸庣敻寮婚垾鎰佸悑闁告劑鍔岄‖澶娾攽閻愬弶鍣藉┑鐐╁亾闂佸搫鐭夌徊鍊熺亽闂佸吋绁撮弲娑氱箔閿熺姵鈷戦柟鑲╁仜閳ь剚娲滈埀顒佺煯閸楀啿顕ｆ繝姘у璺猴功閻ｆ娊姊洪崷顓炲妺闁搞劌鐏氶幈銊╁醇閺囩啿鎷洪梺鍛婄☉閿曘儵鎮″☉銏＄厱閻庯綆鍋呯亸鐢电磼鏉堛劍灏伴柟宄版噺閵堬箓骞愭惔顔瑰亾濡ゅ懏鈷戦柛娑橈功閹冲啴姊虹敮顔惧埌闁伙絿鍏樺鍓佹嫚閻愵剚顥堢€规洏鍎甸幐濠冨緞濡儵鏋呴柣搴ゎ潐濞插繘宕濋幋锔衡偓?base_url 闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈠Χ閸屾矮澹曞┑顔矫畷顒勫储鐎电硶鍋撶憴鍕妞ゎ偄顦遍埀顒勬涧閵堢顕ｉ崼鏇炵闁绘ê鐏氬В搴㈢節閻㈤潧浠╅柟娲讳簽瀵板﹪鎸婃径娑溾偓鍧楁⒑椤掆偓缁夋挳鎮″┑瀣厸闁告劑鍔庢晶娑㈡煟閹垮嫮绉柣鎿冨亰瀹曞爼濡搁敃鈧喊宥夋煟閵忊晛鐏涢柛鏃€鍨垮?
    return {
      id: selectedCfg ? selectedCfg.id : nowId("llm"),
      name: llmNameEl ? llmNameEl.value.trim() : (selectedCfg ? selectedCfg.name : "未命名配置"),
      base_url: llmBaseUrlEl ? llmBaseUrlEl.value.trim() : (selectedCfg ? selectedCfg.base_url : ""),
      api_key: llmApiKeyEl ? llmApiKeyEl.value.trim() : (selectedCfg ? selectedCfg.api_key : ""),
      stream: llmStreamEl ? !!llmStreamEl.checked : true,
      default_model: llmDefaultModelEl ? llmDefaultModelEl.value.trim() : (selectedCfg ? selectedCfg.default_model : null)
    };
  }

  async function loadLLMConfigs() {
    if (llmStatusEl) setText(llmStatusEl, "正在加载配置...");
    try {
      const resp = await window.authFetch("/api/llm/configs");
      const data = await safeJson(resp);
      llmConfigs = data.configs || [];
      llmActive = data.active || { config_id: null, model: null };

      selectedConfigId = (llmActive && llmActive.config_id)
        ? llmActive.config_id
        : (llmConfigs[0] && llmConfigs[0].id);

      renderLLMList();
      const cfg = getSelectedCfg();
      if (cfg) fillLLMEditor(cfg);
      if (llmStatusEl) setText(llmStatusEl, "就绪");
    } catch (error) {
      console.error("加载 LLM 配置失败:", error);
      if (llmStatusEl) setText(llmStatusEl, "加载失败");
    }
  }

  async function saveLLMCfg() {
    const cfg = collectLLMEditor();
    if (!cfg.base_url || !cfg.api_key) {
      alert("请先填写 base_url 和 api_key。");
      return;
    }

    if (llmStatusEl) setText(llmStatusEl, "正在保存配置...");

    const existingConfig = llmConfigs.find(c => c.id === cfg.id);
    const isNewConfig = !existingConfig || !existingConfig.base_url;
    const method = isNewConfig ? "POST" : "PUT";
    const url = method === "PUT"
      ? ("/api/llm/configs/" + encodeURIComponent(cfg.id))
      : "/api/llm/configs";

    const resp = await window.authFetch(url, {
      method,
      body: JSON.stringify(cfg)
    });

    if (!resp.ok) {
      const t = await resp.text();
      if (llmStatusEl) setText(llmStatusEl, "保存失败：" + t);
      return;
    }

    const saved = await resp.json();
    llmConfigs = llmConfigs.filter(c => c.id !== saved.id);
    llmConfigs.push(saved);
    selectedConfigId = saved.id;
    renderLLMList();
    fillLLMEditor(saved);
    if (llmStatusEl) setText(llmStatusEl, "已保存");
  }

  window.saveCurrentLLMConfig = saveLLMCfg;

  async function createLLMCfg() {
    const cfg = {
      id: nowId("llm"),
      name: "新配置",
      base_url: "",
      api_key: "",
      stream: true,
      default_model: ""
    };
    llmConfigs.push(cfg);
    selectedConfigId = cfg.id;
    renderLLMList();
    fillLLMEditor(cfg);
    if (llmStatusEl) setText(llmStatusEl, "已创建，尚未保存");
  }

  async function deleteLLMCfg() {
    const cfg = getSelectedCfg();
    if (!cfg) return;
    if (!confirm("确认删除这条配置吗？")) return;

    if (llmStatusEl) setText(llmStatusEl, "正在删除配置...");
    const resp = await window.authFetch("/api/llm/configs/" + encodeURIComponent(cfg.id), { method: "DELETE" });
    if (!resp.ok) {
      const t = await resp.text();
      if (llmStatusEl) setText(llmStatusEl, "删除失败：" + t);
      return;
    }

    llmConfigs = llmConfigs.filter(c => c.id !== cfg.id);
    selectedConfigId = (llmConfigs[0] && llmConfigs[0].id) || null;
    renderLLMList();
    const selected = getSelectedCfg();
    if (selected) {
      fillLLMEditor(selected);
    }
    if (llmStatusEl) setText(llmStatusEl, "已删除");
  }

  async function setActiveLLM() {
    const cfg = getSelectedCfg();
    if (!cfg) return;

    const model = llmModelSelectEl ? llmModelSelectEl.value : null;
    if (llmStatusEl) setText(llmStatusEl, "正在设为当前配置...");
    const resp = await window.authFetch("/api/llm/active", {
      method: "PUT",
      body: JSON.stringify({ config_id: cfg.id, model })
    });

    if (!resp.ok) {
      const t = await resp.text();
      if (llmStatusEl) setText(llmStatusEl, "设置失败：" + t);
      return;
    }

    llmActive = await resp.json();
    renderLLMList();
    if (llmStatusEl) setText(llmStatusEl, "已设为当前");
  }

  async function refreshModels() {
    const base_url = llmBaseUrlEl ? llmBaseUrlEl.value.trim() : "";
    const api_key = llmApiKeyEl ? llmApiKeyEl.value.trim() : "";
    if (!base_url || !api_key) {
      alert("请先填写 base_url 和 api_key。");
      return;
    }

    if (llmStatusEl) setText(llmStatusEl, "正在检索模型...");
    const resp = await window.authFetch("/api/llm/models/list", {
      method: "POST",
      body: JSON.stringify({ base_url, api_key })
    });

    if (!resp.ok) {
      const t = await resp.text();
      if (llmStatusEl) setText(llmStatusEl, "模型检索失败：" + t);
      return;
    }

    const data = await resp.json();
    const models = data.models || [];

    if (llmModelSelectEl) {
      llmModelSelectEl.innerHTML = "";
      for (const modelName of models) {
        const opt = document.createElement("option");
        opt.value = modelName;
        opt.textContent = modelName;
        llmModelSelectEl.appendChild(opt);
      }

      const cfg = getSelectedCfg();
      const prefer = (llmActive && llmActive.model) || (cfg && cfg.default_model) || (models[0] || "");
      if (prefer && models.includes(prefer)) {
        llmModelSelectEl.value = prefer;
      }
    }

    if (llmStatusEl) setText(llmStatusEl, "模型已更新（" + models.length + "）");
  }

  llmNewBtn && llmNewBtn.addEventListener("click", createLLMCfg);
  llmSaveBtn && llmSaveBtn.addEventListener("click", saveLLMCfg);
  llmDeleteBtn && llmDeleteBtn.addEventListener("click", deleteLLMCfg);
  llmSetActiveBtn && llmSetActiveBtn.addEventListener("click", setActiveLLM);
  llmRefreshModelsBtn && llmRefreshModelsBtn.addEventListener("click", refreshModels);

  // =========================================================
  // Init
  // =========================================================
  function initPresetAndLLM() {
    const hasPresetArea = !!$("tab-presets");
    const hasLLMArea = !!$("tab-api");

    // 缂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾惧綊鏌ｉ幋锝呅撻柛濠傛健閺屻劑寮撮悙娴嬪亾閹间礁鍨傞柛宀€鍋為悡鐔兼煏韫囨洖校闁哥喓鍋ら弻娑氣偓锛卞嫭鐝氶梺鍝勭焿缂嶄線鐛崶顒侇棃婵炴垶锕╁楣冩⒒娴ｅ摜锛嶉柟铏尵缁棃鎮介崹顐㈠簥濠电娀娼ч鍡浰夐崼鐔虹闁瑰鍋熼幊鎰繆椤愮姴鈧繂顫忓ú顏勬嵍妞ゆ挾鍠愰悵顏呯節閻㈤潧浜归柛瀣崌濮婃椽宕崟顓犱紘闂佸摜濮甸幑鍥х暦閻楀牏绡€闁稿鏅崰鎰焽椤忓牆绾ф繛鍡欏亾椤ワ繝姊婚崒姘偓鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偞鐗犻、鏇㈡晜閽樺缃曢梻浣虹《閸撴繈鎽傜€ｎ喖鐐婃い鎺嗗亾缂佺嫏鍕箚妞ゆ劑鍨绘禒娑欎繆閻愯埖顥夐柣锝夘棑缁瑧鎷犻悙顒侇棃闁糕斁鍋撳銈嗗笒閸婅崵澹曟總鍛婄厓闁告繂瀚崳娲煕鐎Ｑ冨⒉缂佺粯鐩畷鍗炍旈崘顏嶅敹婵＄偑鍊曠换鍡涘疾閻樿钃熼柨婵嗩槹閺呮繈鏌嶈閸撶喖鍨鹃敃鈧悾锟犳焽閿旂晫绋?
    if (hasPresetArea) loadPresetsOverview().catch(console.error);
    if (hasLLMArea) loadLLMConfigs().catch(console.error);
  }

  // 缂傚倸鍊搁崐鎼佸磹閻戣姤鍤勯柛顐ｆ礃閹偤骞栧ǎ顒€濡奸柣顓燁殜楠炴牕菐椤掆偓婵¤偐绱掗幇顓ф疁闁哄矉绻濆畷鍫曞煛娴ｅ浄绲块埀顒冾潐濞叉牕顕ｉ崜浣瑰床婵炴垯鍨归獮銏＄箾閸℃〞鎴︽倵閻溾偓闂傚倸鍊搁崐鎼佸磹妞嬪海鐭嗗〒姘ｅ亾妤犵偛顦甸崹楣冨箛娴ｅ湱绋佺紓鍌氬€烽悞锕佹懌闂佸憡鐟ョ换姗€寮婚悢纰辨晬闁挎繂娲ｅЧ妤呮偡濠婂懎顣奸悽顖涘浮閹瑦绻濋崶銊у帗闁荤喐鐟ョ€氼剟宕濋妶鍚ょ懓顭ㄩ崼銏㈡毇闂佸搫鐭夌紞渚€骞冮姀銈呬紶闁告洖鐏氬В澶嬬節閻㈤潧袥闁稿鎸搁湁闁绘挸娴烽幗鐘绘煟閹惧瓨绀嬮柡灞炬礃缁绘繆绠涢弴鐘虫闂備礁鎲＄换鍡椻枍閿濆鐒垫い鎺戝枤濞兼劖绻涢幓鎺旂鐎规洘娲熷濠氬Ψ閵壯呮毎闂備礁鎼崯顐︽偋閸℃稒鍊堕柟鎯板Г閻擄綁鐓崶椋庡埌濞存粍绻堥弻锝呪攽閸パ勮癁濠殿喖锕︾划顖炲箯閸涙潙宸濆┑鐘叉噽椤㈠懘姊绘担钘夊惞闁哥姵鍔栫换娑欑節閸屾粍娈鹃梻渚囧墮缁夋挳鎮″☉銏＄厱閻忕偛澧介埊鏇熺節?
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPresetAndLLM);
  } else {
    initPresetAndLLM();
  }
}
})();



