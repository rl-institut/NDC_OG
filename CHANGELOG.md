# Changelog
All notable changes to this project will be documented in this file.

The format is inpired from [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and the versiong aim to respect [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Here is a template for new release sections

```
## [_._._] - 20XX-MM-DD

### Added
-
### Changed
-
### Removed
-
```
## [Unreleased]

### Added
- Tool citation and impressum (#96)
- Favicon (#97)
- cc0 License for output data (#98)

### Changed
- New banner (#96)
- Rename South America to Central and South America (#95)
- Rename Universal-Energy-Access to Universal-Electricity-Access (#95)
- Colorset for plotting (#97)
- Serve files explicitly with flask (#98)

## [2.0.0] 2019-10-31

### Added

- Specific description for Nigeria (#63)
- Link for Greenwerk (#64)
- Avoid plotting points which have 0% no electricity access (#67)
- Scope for Asia (#67)
- Citation in intro (#72)
- RISE sub indicators (#73)

### Changed

- Now one can select a region by selecting a map
- Display electrification rate in % (#64)
- Instruction in README (#64)
- SE4ALL to uEA (#65)
- Fixed the case where all RISE score are equal to return no shift from baseline (#66)

### Removed
- TIER controls (#73)
## [1.0.0] 2019-09-05

First release

The app features two pages : a static scenarios vizualization and a page with the possibility to alter some of the scenarios input values in a dynamic way.
