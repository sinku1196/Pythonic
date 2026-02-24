credentials_query = """
SELECT ClientID, ExperityUsername, ExperityPassword, ExperityPassphrase
FROM UC_Analytics_Master..ExperityCredentials
WHERE IsActive = 1 AND ClientID = {client_id};
"""
