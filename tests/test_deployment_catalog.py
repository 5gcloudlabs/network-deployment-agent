import unittest

from backend.deployment_catalog import DeploymentCatalog


class DeploymentCatalogTest(unittest.TestCase):
    def test_normalizes_options(self):
        catalog = DeploymentCatalog(
            {
                "version": 1,
                "step_labels": {"sub-prov": "Provision subscribers"},
                "options": [
                    {
                        "id": "free5gc",
                        "type": "kubectl",
                        "category": "single-step",
                        "manifest": "5g/argocd-apps/free5gc-app/free5gc-app.yml",
                        "required_params": ["mcc", "mnc"],
                        "next_step": "sub-prov",
                        "description": "Deploy 5G core only",
                    }
                ],
            }
        )

        option = catalog.get_option("free5gc")

        self.assertEqual(option["github_path"], "5g/argocd-apps/free5gc-app/free5gc-app.yml")
        self.assertEqual(option["required_params"], ["mcc", "mnc"])
        self.assertEqual(catalog.step_labels["sub-prov"], "Provision subscribers")
        self.assertEqual(catalog.options_by_category("single-step")[0]["id"], "free5gc")


if __name__ == "__main__":
    unittest.main()
