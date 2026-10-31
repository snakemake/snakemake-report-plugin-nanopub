# Changelog

## [0.5.1](https://github.com/snakemake/snakemake-report-plugin-nanopub/compare/v0.5.0...v0.5.1) (2026-10-31)


### Bug Fixes

* Pin hatchling core metadata to 2.4 so `twine check` passes in publish job ([8cfc796](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/8cfc796690f8adaf5d1fd1e33beedcb863bac59f))

## [0.5.0](https://github.com/snakemake/snakemake-report-plugin-nanopub/compare/v0.4.0...v0.5.0) (2026-10-30)


### Features

* a proifle error will be raised, if 'np setup' has not been performed ([e041809](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/e04180968475aa93a479d4a36a760cc0e12e54dc))
* profile checking ([5710bd7](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/5710bd7693083e77ff9f9db69d2781316e3c58af))


### Bug Fixes

* added two doc strings ([679bc63](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/679bc633eb8f3c71a26df65949853253fa03a337))
* added two more docstrings ([7cfcd05](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/7cfcd05b24abfa47747ea19e06126780b5625fc3))
* clearer comment ([c7d946f](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/c7d946f5b4db34acf14b76811c55445d51cd2e4c))
* corrected import ([4cc6dab](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/4cc6dabb814c288b086b518c84ae2dd54b15ef3d))
* excluding the changelog from codespell checks ([bd2b2d6](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/bd2b2d6c43760bbf9051575cc34c37703c0e04a7))
* linting ([4d92c6f](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/4d92c6fb34a47ce4d617d0eef69bb5e6acce1b23))
* linting (leftover unused imports and undefined constant ([2ec4d5d](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/2ec4d5d3af634141c2d0908885d11a14df15db32))
* typos and grammar in comment string ([3e43e7d](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/3e43e7daf646f864bec3d71a2badd957a2361aed))

## [0.4.0](https://github.com/snakemake/snakemake-report-plugin-nanopub/compare/v0.3.2...v0.4.0) (2026-10-25)


### Features

* migreated the replease to pixi ([40e1ea6](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/40e1ea6fc0603b3a015a90aff32ce7965aa9db1f))


### Bug Fixes

* ci still contained conda lines ([66bd1e7](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/66bd1e7edb083f3d45ac6f84f328aecaa86cf425))
* concluding merge ([a50f1e9](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/a50f1e9e76a957b2fc7dc113ccb164e762da6120))
* drop poetry/pixi.toml, consolidate into pyproject.toml ([f7a32ad](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/f7a32adc465ee2aa7af43579e906d66b3ad06864))
* pixi migration ready ([7b95d4f](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/7b95d4faa5dbbe82a5aec6d22a7892d1c675010f))
* trying next run with caching ([1ed703b](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/1ed703ba7bfa6ec6fd2bb30772ca8e2c61c856c6))
* typo easyly -&gt; easily ([3d39f87](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/3d39f8704249fdc5649b6c16e1916221795c7fab))

## [0.3.2](https://github.com/snakemake/snakemake-report-plugin-nanopub/compare/v0.3.1...v0.3.2) (2026-08-22)


### Bug Fixes

* corrected version bump for pytest - was typo ([0668d47](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/0668d4747449a535e0bb63245578f204a2bd790c))
* corrected version bump for pytest - was typo ([94c70a7](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/94c70a7ab39b3b18febeb5a3a5d531cf3f6c69fb))

## [0.3.1](https://github.com/snakemake/snakemake-report-plugin-nanopub/compare/v0.3.0...v0.3.1) (2026-06-12)


### Bug Fixes

* added nanopub hashtag to the announcement message ([70916c3](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/70916c38aeb420b9264aabe584438d912a00ca68))
* added nanopub hashtag to the announcement message ([c7125ae](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/c7125aea0dbc9af418244da863a9cdee1111ce57))
* PLugin -&gt; Plugin ([cfade62](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/cfade62d427dfc0fc614037f700635b2366d8555))
* PLugin -&gt; Plugin ([42a75a3](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/42a75a36ac6eebef509f7cf45ebbeb5a419c3a4a))
* pytest version minimal 9.0.3 ([b033f9b](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/b033f9b2db6d9ca3e895e3e1955801ff9065162c))
* pytest version minimal 9.0.3, due security issue - pytest through 9.0.2 on UNIX relies on directories with the '/tmp/pytest-of-{user}' name pattern, which allows local users to cause a denial of service or possibly gain privileges. ([171000e](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/171000e1dd35b544102b3a586adba374f455a1cb))

## [0.3.0](https://github.com/snakemake/snakemake-report-plugin-nanopub/compare/v0.2.0...v0.3.0) (2026-06-08)


### Features

* stable graphviz format ([4d74582](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/4d74582346d4584ad05d485613f6cd9c7b3a6d2f))


### Bug Fixes

* dependabot ([31d3f9d](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/31d3f9dbde338debd1dcea5ed987249dadcdb4c1))
* removed unused import ([e2c51da](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/e2c51da08efa0451cb918fad57188e45837f31b0))


### Documentation

* updated readme and added test ([83bae80](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/83bae8027562190fff39ee010dfb26ceca1227d9))

## [0.2.0](https://github.com/snakemake/snakemake-report-plugin-nanopub/compare/v0.1.0...v0.2.0) (2026-05-05)


### Features

* added pyaml deps ([a40892c](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/a40892c5c855d26d39fcefb6736accee78f36afc))


### Bug Fixes

* catching additional ([559bea1](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/559bea1f7eeed3ae9b52e94f86ce117951a6214b))
* formatting ([e054733](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/e0547333f2c4fdfa098f6c4c2295c09a47fd026a))
* formatting & linting ([721bd9d](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/721bd9dc97530cb8dbda16c84017842e517cfe9b))
* now conda env versions are present, so are wrapper versions ([d11ce70](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/d11ce70971848bb6fc24ee114bbd59454ebdb7a4))
* rule info from job stats to rule metadata ([5302862](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/53028624f3a2013d5182a47dcda03f899cdc8978))
* stable in- output extraction ([5362b47](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/5362b47f173d2e7c2627d42181b5baac5e7d6393))
* test string ([3ffc08d](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/3ffc08d0c7135e1f65a9fe52ad41221ffc44fabd))
* typos ([d7db6ab](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/d7db6ab4bab8d63d25ab790af03bdfadb801f0f3))
* typos ([962a39a](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/962a39ac730f8bf9e49b50f6ad51e74e7cd379a0))
* wrapper version, in- and output are stored, no job stats anymore - tests adapted ([d5dc802](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/d5dc80267bf84028e8d6dbfc81c22a45bff76671))

## 0.1.0 (2026-04-21)


### Features

* added announcement CI plus logo image ([8124fc7](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/8124fc72793ee390222cff9a0df80c1a9706ced2))
* added basic code (automatic scaffold by poetry) ([a81a92f](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/a81a92f6fc699f0054bd992d27579513d01cce33))
* added basic test code (auto generated by poetry ([5858e76](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/5858e7632e4efbddf8834f759b5a3278648e2aa2))
* added cli script for plotting dependency graphs ([d887696](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/d88769659066e4c442ce85f7c0af6d8f8f6f7aa6))
* added coverage tests for pixi ([21488dc](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/21488dcd807d5d0a127d6f85fcdbe7a274c55e21))
* added dependencies ([179d86f](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/179d86f0724c87b3fdf58a8f0329fc5a80a3860e))
* added example knowledge graph image ([792f6db](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/792f6dba43ff52159e3a48d39acacaed0682bb7e))
* cli now considering workflow metadata ([2ad0f1b](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/2ad0f1b8e6b6d42cc0d7a9c4f139b615344ddac5))
* coded skeleton - untested ([aa4f0ec](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/aa4f0ec4364f8507c39969b4d8a9ee79e46c9ed7))
* consider testing the graph file, too ([cfc2496](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/cfc2496bebfec14671537fbf9baa65773ebd524c))
* documenting --workflow-configuration-id ([5e60c84](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/5e60c846e08be9b5cf4b533ce66495a19e382416))
* first working version ([75d6821](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/75d68212077e06939fcf8582e0e6bc8812e8c861))
* improved balance between published quads and limits ([db8d18b](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/db8d18bb3fba523f640813fa4ba2eec4884665f2))
* included nanopub py as a dependency ([37ae247](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/37ae247e628274875c488d09a65b236d81a432cb))
* shrinking content size by stripping comments ([a4089cf](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/a4089cf1f74df31f8a0420b677c2dd35d6dc6878))
* signedby attribute was added ([1a7511c](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/1a7511cb40a2d141a411a5441b1c9cc4da866309))
* stabilized plotting ([7bab5c1](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/7bab5c158e8e42a5a5c6aac259c6fecb66f9b17e))
* version 1 ([9bb126e](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/9bb126e617dc3b51c1066cf4805f3c52bf050d66))
* working version ([c85ecd7](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/c85ecd78498a42d90b7e0e2498fc4f5957ba83ce))
* working version - needs polishing ([0ba4c51](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/0ba4c51dfe4dd152e9f45897b966236472224651))
* working version - not yet structured ([7ef3899](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/7ef38992ee2f86bf6e40845a27594ba0e0f10d1f))


### Bug Fixes

* added pixi information to toml files ([22b70e6](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/22b70e6c2d1b7c6eaf9401bf0267d27711f3eed5))
* attempt 2 - should fail in tests, as no nanopub-py is installed, waiting for the new version ([0b85a68](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/0b85a68cff6c7960f26febe40cc0d1edd0aaa4e6))
* bumped python dep in CI to 3.12 for compatibility checks ([a6c4f0e](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/a6c4f0e7e4c99dc29acca7545db6a8687239f2a5))
* bumped snakemake version to something recent ([136e003](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/136e00367efe87ee325df971bd81a389506fbd87))
* corrected description handling ([c747028](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/c7470285f9e671d94b5b5ed9404e3151c45bfdec))
* docstring typo ([ca1f853](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/ca1f853f9aa84667a36f5360e1de8c21bce31003))
* fixes the pixi CI issue - hopefully ([a426c98](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/a426c9820b9c33213320d2f441ed8cbf55cbcba5))
* formatting ([b65d1a0](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/b65d1a0bcc9c213d508e3d27c802c215dbf359ef))
* formatting ([dbdd216](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/dbdd216bd492ff33e7971f52ba07726a5f4ff370))
* formatting ([2f62d66](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/2f62d6699f786115600cc1925c3b217927ec9a35))
* formatting ([e12b70c](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/e12b70c0238271c51e97fc4f30fa2ee334d4816a))
* formatting ([4dd16a4](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/4dd16a4a5479b86b2e5787b9462e05a40944fe2c))
* formatting ([e4004ba](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/e4004ba70b8beadd92c0aa3b741e2bf10cd67933))
* formatting ([e99f991](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/e99f991ea544391b37c9758802f820d494c59557))
* formatting ([be4dbf2](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/be4dbf2e82e129537eb80b27c6fbdc0326314e6c))
* linint - removed unused import ([30f4dd2](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/30f4dd2f84d906b1dd53051c58041a10cf5e7635))
* linting ([54148e8](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/54148e8740e7e183f6ca7d0f70202810d0200bba))
* merge conflict ([d793fd4](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/d793fd46fa4ebe54d53ab83d49f70ac53e211c2c))
* name ([696215c](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/696215c31ee1f1bf2aee2055fe7a25648607537b))
* nanopub-py is a pypi not a conda dep ([a291029](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/a291029da2207360018cd6272de8500a0a4542e6))
* relaxing system requirements to work on cluster envs ([04c4276](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/04c4276e353c9f7e6488487f615d2efe5169c6ac))
* removed unused import ([405caf0](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/405caf088f92f6e6c47a936d217f8c63b45fd48a))
* reverting to snakemake's global logger, added comments ([a245dc3](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/a245dc3d26a4a1efb615df7ace092d5806b24b98))
* somewhat improved string handling to comply with all tests ([716deb1](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/716deb10d14f7fc8e00dfd26825744b2466de5d2))
* spelling ([55f4a49](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/55f4a499f59dddfd4e8b3b92f4e886106453b46d))
* stripping html tags from workflow description ([8e49dce](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/8e49dcee0641f81a0246198fef9bd967b9db4007))
* switching to 'Dataset() from 'ConjunctiveGraph()' to avoid deprecation warnings ([1604bfb](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/1604bfb5096c2a82b515ac538692ac7dea9c50fd))
* test dependencies ([e32da0f](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/e32da0fe7a15566f05ccf49f98d86eddde3f2c2e))
* testing ([c07a189](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/c07a18900dd71fd612f97f3f25d033335d62bc4d))
* typo ([66b19a2](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/66b19a2eba0754e48074b0a231130515a91baf4c))


### Documentation

* added actual documentation ([0a6a619](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/0a6a619245e06a4be8d4393d813c633c8066d413))
* added intro section about nanopublications ([21fe950](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/21fe950d50a706aa2dd70bfc0fb65890ece30ad5))
* first rough README ([94853a2](https://github.com/snakemake/snakemake-report-plugin-nanopub/commit/94853a28ebae76d29c0261b2f6f3fa85f898a60f))
