# CoffeeRoast Deployment

Run the deployment script from the repository root:

```bash
./deploy/deploy.sh
```

The script builds `iRoastControl Software/iRoastControl.sln` in `Release` mode and copies the contents of `iRoastControl Software/bin/Release` to `~/coffeeroastbuild`.

You can override the destination if needed:

```bash
DEST_DIR=/tmp/coffeeroastbuild ./deploy/deploy.sh
```

Requirements:

- MSBuild from Visual Studio Build Tools, or Mono `xbuild`
- `nuget` when the `packages/` directory has not already been restored
