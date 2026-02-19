# Databricks Transform App

A React + Flask application that takes an origin and destination from the user, runs a transform query on Databricks, and displays the results.

## Project Structure

```
├── frontend/          # React (Vite) frontend
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── TransformForm.jsx   # Origin/destination input form
│           └── ResultsTable.jsx    # Query results display
├── backend/           # Python Flask backend
│   ├── app.py         # API server
│   ├── transform.py   # Databricks query logic
│   └── .env.example   # Environment variable template
```

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and fill in your Databricks credentials
cp .env.example .env
# Edit .env with your values

python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:3000` and proxies API requests to the Flask backend on port 5000.

## Configuration

Edit `backend/.env` with your Databricks credentials:

| Variable | Description |
|---|---|
| `DATABRICKS_SERVER_HOSTNAME` | Your workspace hostname (e.g. `adb-123.azuredatabricks.net`) |
| `DATABRICKS_HTTP_PATH` | SQL warehouse HTTP path |
| `DATABRICKS_ACCESS_TOKEN` | Personal access token |
| `DATABRICKS_CATALOG` | Unity Catalog name (default: `main`) |
| `DATABRICKS_SCHEMA` | Schema name (default: `default`) |

## Customizing the Query

Edit `backend/transform.py` — the `build_query()` function — to change the table name, columns, or transformation logic to match your Databricks schema.
