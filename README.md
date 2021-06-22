This is a minimal Python wrapper around the App Center REST APIs to get you up and running. If you are looking for something more substantial, please refer to the REST API documentation: https://openapi.appcenter.ms/

You can install with `pip install appcenter`

## Usage

```python
# 1. Import the library
import appcenter

# 2. Create a new client
client = appcenter.AppCenterClient(access_token="abc123def456")

# 3. Check some error groups
start = datetime.datetime.now() - datetime.timedelta(days=10)
for group in client.crashes.get_error_groups(owner_name="owner", app_name="myapp", start_time=start):
    print(group.errorGroupId)
    
# 4. Get recent versions
for version in client.versions.all(owner_name="owner", app_name="myapp"):
    print(version)
    
# 5. Create a new release
client.versions.upload_and_release(
    owner_name="owner",
    app_name="myapp",
    version="0.1",
    build_number="123",
    binary_path="/path/to/some.ipa",
    group_id="12345678-abcd-9012-efgh-345678901234",
    release_notes="These are some release notes",
    branch_name="test_branch",
    commit_hash="1234567890123456789012345678901234567890",
    commit_message="This is a commit message"
)
```

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
