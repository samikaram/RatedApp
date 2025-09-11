def modify_models():
    # Read the entire current file
    with open('rated_app/patient_rating/models.py', 'r') as f:
        content = f.readlines()

    # Add SOFTWARE_CHOICES and AUTH_TYPES at the top after imports
    import_index = -1
    for i, line in enumerate(content):
        if 'from django.core.validators import MinValueValidator, MaxValueValidator' in line:
            import_index = i
            break

    if import_index != -1:
        # Insert choices after the last import
        choices_to_add = [
            "\n# Software Integration Choices\n",
            "SOFTWARE_CHOICES = [\n",
            "    ('cliniko', 'Cliniko'),\n",
            "    ('pracsuite', 'PracSuite'),\n",
            "    # Future software options can be added here\n",
            "]\n\n",
            "AUTH_TYPES = [\n",
            "    ('basic', 'Basic Authentication'),\n",
            "    ('oauth2', 'OAuth 2.0'),\n",
            "    ('api_key', 'API Key')\n",
            "]\n\n"
        ]
        
        for choice in reversed(choices_to_add):
            content.insert(import_index + 1, choice)

    # Find the RatedAppSettings class
    ratedappsettings_start = None
    ratedappsettings_end = None
    for i, line in enumerate(content):
        if 'class RatedAppSettings(models.Model):' in line:
            ratedappsettings_start = i
        if ratedappsettings_start is not None and 'class ' in line and i > ratedappsettings_start:
            ratedappsettings_end = i
            break

    if ratedappsettings_start is None or ratedappsettings_end is None:
        print("Could not find RatedAppSettings class")
        return

    # Construct new class content
    new_class_content = content[ratedappsettings_start:ratedappsettings_end]

    # Find where to insert new fields (before created_at)
    insert_index = -1
    for i, line in enumerate(new_class_content):
        if 'created_at = models.DateTimeField(auto_now_add=True)' in line:
            insert_index = i
            break

    if insert_index == -1:
        print("Could not find created_at field")
        return

    # New fields to add (keeping existing fields intact)
    new_fields = [
        "\n    # NEW SOFTWARE INTEGRATION FIELDS\n",
        "    software_type = models.CharField(\n",
        "        max_length=50, \n",
        "        choices=SOFTWARE_CHOICES, \n",
        "        default='cliniko',\n",
        "        verbose_name=\"Software Type\"\n",
        "    )\n\n",
        "    base_url = models.URLField(\n",
        "        max_length=300, \n",
        "        default='https://api.au1.cliniko.com/v1/',\n",
        "        verbose_name=\"API Base URL\"\n",
        "    )\n\n",
        "    auth_type = models.CharField(\n",
        "        max_length=20, \n",
        "        choices=AUTH_TYPES, \n",
        "        default='basic',\n",
        "        verbose_name=\"Authentication Type\"\n",
        "    )\n\n",
        "    additional_config = models.JSONField(\n",
        "        null=True, \n",
        "        blank=True,\n",
        "        verbose_name=\"Additional Configuration\"\n",
        "    )\n\n"
    ]

    # Insert new fields
    for field in reversed(new_fields):
        new_class_content.insert(insert_index, field)

    # Update __str__ method
    for i, line in enumerate(new_class_content):
        if 'return f"{self.clinic_name} Settings"' in line:
            new_class_content[i] = '        return f"{self.clinic_name} Settings ({self.software_type})"\n'
            break

    # Replace the old class content with new content
    content[ratedappsettings_start:ratedappsettings_end] = new_class_content

    # Write back to file
    with open('rated_app/patient_rating/models.py', 'w') as f:
        f.writelines(content)

    print("✅ Modifications completed successfully")
    print("✅ Existing fields preserved")
    print("✅ New integration fields added")

if __name__ == "__main__":
    modify_models()
