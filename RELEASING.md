# Releasing guidata

> **Golden rule: never create a GitHub release by hand.** Push the tag, wait for the draft release prepared by the CI, then publish that draft.

A release takes two steps, both run by [`.github/workflows/release.yml`](.github/workflows/release.yml), which relies on the [release actions](https://github.com/DataLab-Platform/release-actions) shared by the DataLab Platform projects:

1. **Prepare**: pushing a release tag checks the tag, runs the tests, builds the wheel and the sdist (with compiled translations), attests their build provenance and creates a **draft** GitHub release with these files and their `SHA256SUMS`. Nothing is published at this stage.
2. **Publish**: when a maintainer publishes the draft release, its files are checked (checksums and attestations) and uploaded to PyPI. A release created by hand has none of these files, so nothing is uploaded.

## One-time prerequisites

* **PyPI**: Trusted Publisher for `guidata` with owner `PlotPyStack`, repository `guidata`, workflow `release.yml` and environment `pypi`.
* **TestPyPI** (release candidates): the same Trusted Publisher on [test.pypi.org](https://test.pypi.org/) with environment `testpypi`.
* **GitHub**: the `pypi` and `testpypi` environments only accept release tags (`v[0-9]*.[0-9]*.[0-9]*`).

## Releasing a final version

1. On `develop` (through a pull request as usual):
   * set `__version__ = "X.Y.Z"` in `guidata/__init__.py`;
   * write the `## guidata Version X.Y.Z ##` section of `doc/release_notes/release_X.YY.md`: it becomes the description of the GitHub release, and the release is refused if it is missing.
2. Merge `develop` into `master`.
3. Tag `master` and push the tag (`-s` signs the tag, use `-a` otherwise):

   ```console
   git switch master
   git pull
   git tag -s vX.Y.Z -m "guidata vX.Y.Z"
   git push origin vX.Y.Z
   ```

4. Follow the **Prepare vX.Y.Z** run in the [Actions](https://github.com/PlotPyStack/guidata/actions/workflows/release.yml) tab. When it succeeds, its summary links to the draft release.
5. Review the draft release (title, description, files: wheel, sdist and `SHA256SUMS`), then click **Publish release**.
6. Publishing starts the **Publish vX.Y.Z** run, which uploads the files to [PyPI](https://pypi.org/project/guidata/).

## Release candidates

A tag `vX.Y.Z-rcN` (for example `v3.18.0-rc1`) follows the same two steps, with these differences:

* `__version__` must be `"X.Y.ZrcN"` (for example `"3.18.0rc1"`), and the tag may be on any branch;
* the release notes section is optional;
* the draft release is marked as a pre-release, and publishing it uploads the files to [TestPyPI](https://test.pypi.org/project/guidata/) only.

Release candidates are the way to rehearse the procedure, or to check a change of the release workflow, without publishing anything on PyPI. To install a release candidate:

```console
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ guidata==X.Y.ZrcN
```

## When something goes wrong

| Symptom | What to do |
| --- | --- |
| The **Prepare** run fails (tag, version, release notes, tests or build) | Nothing was published. Delete the tag (`git push --delete origin vX.Y.Z`, then `git tag -d vX.Y.Z`), fix the problem, then tag again. A draft release left by a failed attempt is replaced automatically. |
| A problem is found while reviewing the draft release | Delete the draft release and the tag, fix the problem, then tag again. Nothing was published. |
| The **Prepare** run fails with "Release already published" | A release was created by hand for this tag. Delete it, then re-run the failed jobs of the **Prepare** run. If immutable releases are enabled on the repository, the tag cannot be reused: release version X.Y.Z+1 instead. |
| The **Publish** run fails with "Release not prepared by the release workflow" | The published release was created by hand. Nothing was uploaded to PyPI: delete the release, then re-run the **Prepare** run of the tag (or, with immutable releases, release version X.Y.Z+1). |
| The **Publish** run fails while uploading (PyPI error, Trusted Publisher not configured…) | Fix the cause, then click **Re-run failed jobs** on the run: the files are checked again, and files already uploaded are skipped. |

## Why this procedure

* The upload to PyPI, which cannot be undone, comes last, after a maintainer has reviewed the draft release.
* PyPI receives exactly the files attached to the GitHub release, built and attested by the release workflow.
* The files are attached before the release is published, as required by immutable releases.
* The same procedure applies to the other DataLab Platform projects (see the [release actions](https://github.com/DataLab-Platform/release-actions)).