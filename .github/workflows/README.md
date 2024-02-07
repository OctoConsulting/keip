# Github Actions
This monorepo consists of 3 artifacts that are versioned, built, and released separately.
- minimal-app
- operator
- operator/webhook

## PR builds
When a PR is opened or updated, it will determine if any files changed in each of the sub-project directories.
If a file has changed it will trigger a build for that sub-project which runs a number of checks.

## Releasing
Release builds are triggered when code is merged to the main branch.
It will also listen to each subdirectory and run the respective release job for each sub-project if any changes were found.

To perform a new release, simply update the version for a given subproject.
The version can be found either in a version.txt file or pom.xml file at the root of each subproject.
New releases of the same version will never overwrite old releases.
If the intent is to overwrite an old github release or docker image package, then the old artifact and its associated git tags should be deleted first.
If a previous attempt at release failed, it can be re-ran by going to the github actions tab, choose the job that failed, click re-run on the top right, and either run all jobs or failed jobs.

## Caching
There is currently no caching for builds, but it could be added at a later date.
