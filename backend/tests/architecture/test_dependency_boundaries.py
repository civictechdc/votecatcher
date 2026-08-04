import pytest
from archunitpython import assert_passes, project_files


def test_production_code_has_no_import_cycles():
    rule = (
        project_files("app/")
        .in_folder("**")
        .should()
        .have_no_cycles()
        .because("cycles hide dependency direction and prevent isolated behavior tests")
    )

    assert_passes(rule)


@pytest.mark.parametrize(
    "outer_folder",
    [
        "routers/**",
        "services/**",
        "jobs/**",
        "files/**",
        "persistence/**",
        "data/**",
        "repositories/**",
    ],
)
def test_domain_does_not_depend_on_outer_layers(outer_folder: str):
    rule = (
        project_files("app/")
        .in_folder("domain/**")
        .should_not()
        .depend_on_files()
        .in_folder(outer_folder)
        .because(
            "domain policy must remain independent of transport and infrastructure"
        )
    )

    assert_passes(rule)


@pytest.mark.parametrize(
    "external_module",
    ["fastapi", "sqlmodel", "openai", "mistralai", "google.genai"],
)
def test_domain_does_not_depend_on_framework_or_provider_modules(external_module: str):
    rule = (
        project_files("app/")
        .in_folder("domain/**")
        .should_not()
        .depend_on_external_modules()
        .matching(external_module)
        .because("domain policy must not couple to frameworks or external providers")
    )

    assert_passes(rule)


@pytest.mark.parametrize("outer_folder", ["data/**", "persistence/**"])
def test_routers_do_not_depend_on_data_or_persistence(outer_folder: str):
    rule = (
        project_files("app/")
        .in_folder("routers/**")
        .should_not()
        .depend_on_files()
        .in_folder(outer_folder)
        .because("HTTP adapters must delegate persistence work to application services")
    )

    assert_passes(rule)


def test_services_do_not_depend_on_routers():
    rule = (
        project_files("app/")
        .in_folder("services/**")
        .should_not()
        .depend_on_files()
        .in_folder("routers/**")
        .because("application services must remain independent of HTTP adapters")
    )

    assert_passes(rule)
