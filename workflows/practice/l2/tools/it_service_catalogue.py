from workflows.practice.l2.models import SupportCategory


IT_SERVICE_CATALOGUE = {
    SupportCategory.security: "Cyber Security Operations",
    SupportCategory.vpn: "Network Operations",
    SupportCategory.email: "Email Support",
    SupportCategory.hardware: "Hardware Support",
    SupportCategory.software: "Software Support",
    SupportCategory.identity: "Identity Management",
    SupportCategory.network: "Network Operations",
    SupportCategory.other: "General IT Support",
}


def get_support_team(
    category: str,
    security_related: bool,
) -> str:
    """Retrieve the support team responsible for a given category."""

    if security_related:
        return IT_SERVICE_CATALOGUE.get(SupportCategory.security, "Cyber Security Operations")

    return IT_SERVICE_CATALOGUE.get(SupportCategory(category), "General IT Support")
