# Contributing to ZX Anim

## Maintaining Documentation

Update `README.md` whenever a change affects installation, controls, OBS
setup, character pack structure, or the development workflow.

For a normal feature update:

1. Update **Features** when user-visible behavior changes.
2. Update **Controls** when shortcuts or input behavior change.
3. Update **OBS Setup** when the capture workflow changes.
4. Update **Custom Characters** when the manifest format changes.
5. Update **Build** when dependencies or packaging commands change.
6. Replace `preview/preview.gif` when the interface or default animation
   changes significantly.

Keep the README focused on current behavior. Historical changes belong in
GitHub Release notes.

## Release Checklist

1. Update `zxanim/__init__.py` with the new semantic version.
2. Update the fallback `AppVersion` in `installer/zx_anim.iss`.
3. Update `README.md` if user-facing behavior changed.
4. Run the tests and build:

   ```powershell
   python -m unittest discover -s tests
   pyinstaller --clean --noconfirm zx_anim.spec
   ```

5. Commit and push the changes.
6. Create and push a matching version tag:

   ```powershell
   git tag -a v3.0.0 -m "Release v3.0.0"
   git push origin main
   git push origin v3.0.0
   ```

The tag version is passed to Inno Setup automatically by the release workflow.
