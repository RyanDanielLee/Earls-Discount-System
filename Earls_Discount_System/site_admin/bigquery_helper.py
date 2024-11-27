from google.cloud import bigquery

def fetch_bigquery_data(query):
    client = bigquery.Client()

    query_job = client.query(query)
    results = query_job.result()

    data = [dict(row) for row in results]
    return data