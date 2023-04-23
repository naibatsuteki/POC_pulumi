"""An Azure RM Python Pulumi program"""
from pathlib import Path

import jinja2
import pulumi
from pulumi_azure_native import storage
from pulumi_azure_native import resources

# Get current stack info
current_stack = pulumi.get_stack()
template_file = Path("assets/templates/index.html")
result_file = Path("dist/index.html")

data = {
    "stack_name": current_stack
}

# Load the Jinja template
with open(template_file, "r") as file:
    template = jinja2.Template(file.read())


# Render the template with the data
rendered_template = template.render(data)


# Write the rendered template to a file
result_file.parent.mkdir(parents=True, exist_ok=True)
with open(result_file, "w") as file:
    file.write(rendered_template)

# Create an Azure Resource Group
resource_group = resources.ResourceGroup(
    "resource_group",
    resource_group_name=f"{current_stack}pulumiqs"
    )

# Create an Azure resource (Storage Account)
account = storage.StorageAccount(
    "sa",
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(
        name=storage.SkuName.STANDARD_LRS,
    ),
    kind=storage.Kind.STORAGE_V2,
    account_name=f"{current_stack}pulumiqs"
)

# Enable static website support
static_website = storage.StorageAccountStaticWebsite(
    "staticWebsite",
    account_name=account.name,
    resource_group_name=resource_group.name,
    index_document="index.html",
    error404_document="",
)

# Export the primary key of the Storage Account
primary_key = (
    pulumi.Output.all(resource_group.name, account.name)
    .apply(
        lambda args: storage.list_storage_account_keys(
            resource_group_name=args[0], account_name=args[1]
        )
    )
    .apply(lambda accountKeys: accountKeys.keys[0].value)
)

pulumi.export("primary_storage_key", primary_key)

# Upload the file
index_html = storage.Blob(
    "index.html",
    resource_group_name=resource_group.name,
    account_name=account.name,
    container_name=static_website.container_name,
    source=pulumi.FileAsset(result_file),
    content_type="text/html",
)

# Web endpoint to the website
pulumi.export("staticEndpoint", account.primary_endpoints.web)
