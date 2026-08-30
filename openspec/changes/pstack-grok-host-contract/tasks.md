## 1. Specs

- [x] 1.1 OpenSpec change `pstack-grok-host-contract` with spawn, enable, README locale, inspect count.
- [x] 1.2 `openspec validate pstack-grok-host-contract --type change --strict` from this repo.

## 2. README locale

- [x] 2.1 English `README.md` plus `README.zh-CN.md` and switcher.
- [x] 2.2 Scanners skip `README.zh-CN.md` and `.superpowers`.
- [x] 2.3 `test_readme_locale_split`.

## 3. Spawn types

- [x] 3.1 Skills and HARNESS spawn `pstack:<role-key>`.
- [x] 3.2 Setup writes `~/.grok/roles/pstack:<key>.toml`.
- [x] 3.3 `test_grok_spawn_types_are_plugin_qualified`.

## 4. Enable and TEST-PLAN

- [x] 4.1 README names `[plugins].enabled`, EROFS, `grok --sandbox off plugin enable pstack`.
- [x] 4.2 TEST-PLAN Gate 1 counts `.agents[]`, not `provides.agents`.

## 5. Catalog follow-up

- [x] 5.1 After this lands on pstack `main`, pin `grok-build-plugins` sha and document enable there. Catalog pin tracks origin/main (8ea3830 at close of that follow-up; later pins follow later landings). Enable is documented in grok-build-plugins README.
