# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo
from google.cloud import firestore

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from .a2ui_utils import a2ui_callback



async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except ValueError:
        pass
    return None




# Hardcoded project ID for Firestore client
PROJECT_ID = "qwiklabs-gcp-01-549c7ea1926b"
db = firestore.Client(project=PROJECT_ID)


def get_portfolio() -> list[dict]:
    """Retrieves all current investment portfolio holdings from Firestore.

    Returns:
        A list of dictionaries representing portfolio holdings.
    """
    holdings_ref = db.collection("holdings")
    docs = holdings_ref.stream()
    holdings = [doc.to_dict() for doc in docs]
    return holdings


def add_or_update_holding(ticker: str, name: str, shares: float, avg_price: float, asset_class: str = "Equities") -> str:
    """Adds a new stock or asset holding to the portfolio in Firestore or updates an existing one.

    Args:
        ticker: The stock ticker symbol (e.g. 'AAPL', 'GOOGL', 'NVDA').
        name: The full company or asset name.
        shares: Number of shares owned.
        avg_price: Average purchase price per share.
        asset_class: Category of asset (e.g. 'Equities', 'ETF', 'Crypto').

    Returns:
        Confirmation message of the updated holding.
    """
    doc_id = ticker.upper()
    data = {
        "ticker": doc_id,
        "name": name,
        "shares": float(shares),
        "avg_price": float(avg_price),
        "asset_class": asset_class,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    db.collection("holdings").document(doc_id).set(data)
    return f"Successfully saved holding {doc_id} ({name}) with {shares} shares at ${avg_price:.2f}."


def get_transactions(limit: int = 10) -> list[dict]:
    """Retrieves recent recorded expenses and income transactions from Firestore.

    Args:
        limit: Maximum number of transactions to retrieve (default: 10).

    Returns:
        A list of recent transaction dictionaries.
    """
    tx_ref = db.collection("transactions").limit(limit)
    docs = tx_ref.stream()
    return [doc.to_dict() for doc in docs]


def log_transaction(amount: float, category: str, description: str) -> str:
    """Logs a new expense or financial transaction into Firestore.

    Args:
        amount: Dollar amount of transaction.
        category: Expense or income category (e.g. 'Groceries', 'Investment', 'Rent', 'Utilities').
        description: Brief description of the transaction.

    Returns:
        Confirmation message of logged transaction.
    """
    data = {
        "amount": float(amount),
        "category": category,
        "description": description,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    doc_ref = db.collection("transactions").add(data)
    return f"Successfully logged transaction of ${amount:.2f} under category '{category}' (ID: {doc_ref[1].id})."


def get_stock_quote(ticker: str) -> dict:
    """Looks up current market data and simulated stock quote for a given ticker symbol.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL', 'GOOGL', 'NVDA', 'VTI').

    Returns:
        A dictionary containing current price, daily change, and valuation metrics.
    """
    symbol = ticker.upper()
    quotes = {
        "AAPL": {"ticker": "AAPL", "price": 232.50, "change_pct": "+1.4%", "market_cap": "3.5T", "pe_ratio": 33.2},
        "GOOGL": {"ticker": "GOOGL", "price": 182.10, "change_pct": "+0.8%", "market_cap": "2.2T", "pe_ratio": 24.1},
        "NVDA": {"ticker": "NVDA", "price": 128.40, "change_pct": "+2.9%", "market_cap": "3.1T", "pe_ratio": 45.6},
        "VTI": {"ticker": "VTI", "price": 274.20, "change_pct": "+0.5%", "market_cap": "1.6T", "pe_ratio": 21.0}
    }
    if symbol in quotes:
        return quotes[symbol]
    return {
        "ticker": symbol,
        "price": 150.00,
        "change_pct": "0.0%",
        "market_cap": "N/A",
        "pe_ratio": 20.0
    }


def fetch_market_news(query_or_ticker: str, limit: int = 5) -> list[dict]:
    """Fetches real-time financial market news headlines for a given company, ticker, or financial topic.

    Args:
        query_or_ticker: Stock ticker symbol or financial query (e.g. 'NVDA', 'Apple stock', 'Federal Reserve').
        limit: Maximum number of news articles to return (default: 5).

    Returns:
        A list of dictionaries containing article title, link, and publication date.
    """
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET

    search_term = f"{query_or_ticker} stock finance"
    encoded_query = urllib.parse.quote(search_term)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    try:
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")[:limit]

        articles = []
        for item in items:
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")

            articles.append({
                "title": title_elem.text if title_elem is not None else "No Title",
                "link": link_elem.text if link_elem is not None else "",
                "pub_date": pub_date_elem.text if pub_date_elem is not None else ""
            })
        return articles
    except Exception as e:
        return [{"error": f"Failed to fetch market news: {str(e)}"}]


def calculate_financial_projection(principal: float, monthly_contribution: float, annual_return_pct: float, years: int) -> dict:
    """Calculates future investment growth and compound interest trajectory over time.

    Args:
        principal: Initial investment amount in dollars.
        monthly_contribution: Recurring monthly deposit amount in dollars.
        annual_return_pct: Expected annual return rate percentage (e.g. 7.0 for 7%).
        years: Total investment horizon in years.

    Returns:
        A dictionary with final portfolio balance, total interest earned, total principal deposited, and yearly milestone values.
    """
    monthly_rate = (float(annual_return_pct) / 100.0) / 12.0
    total_months = int(years) * 12
    current_balance = float(principal)
    total_deposited = float(principal)
    yearly_milestones = []

    for month in range(1, total_months + 1):
        interest_this_month = current_balance * monthly_rate
        current_balance += interest_this_month + float(monthly_contribution)
        total_deposited += float(monthly_contribution)

        if month % 12 == 0:
            year_num = month // 12
            yearly_milestones.append({
                "year": year_num,
                "balance": round(current_balance, 2),
                "total_deposited": round(total_deposited, 2),
                "interest_earned": round(current_balance - total_deposited, 2)
            })

    return {
        "final_balance": round(current_balance, 2),
        "total_principal": round(total_deposited, 2),
        "total_interest_earned": round(current_balance - total_deposited, 2),
        "years": int(years),
        "yearly_breakdown": yearly_milestones
    }


def get_currency_exchange_rates(base_currency: str = "USD", target_currencies: str = "EUR,GBP,JPY,CAD,AUD") -> dict:
    """Fetches real-time foreign exchange currency rates from a free public financial API.

    Args:
        base_currency: Base 3-letter currency code (e.g. 'USD', 'EUR', 'GBP'). Default is 'USD'.
        target_currencies: Comma-separated list of target currency codes (e.g. 'EUR,GBP,JPY,CAD,AUD').

    Returns:
        A dictionary containing base currency, rates for target currencies, and last update timestamp.
    """
    import json
    import os
    import urllib.request

    base = base_currency.upper().strip()
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    url = f"https://open.er-api.com/v6/latest/{base}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("result") != "success":
            return {"error": f"Exchange rate lookup failed for base currency '{base}'"}

        all_rates = data.get("rates", {})
        targets = [c.strip().upper() for c in target_currencies.split(",") if c.strip()]

        filtered_rates = {t: all_rates[t] for t in targets if t in all_rates}

        return {
            "base_currency": base,
            "rates": filtered_rates,
            "time_last_update_utc": data.get("time_last_update_utc", "")
        }
    except Exception as e:
        return {"error": f"Failed to fetch exchange rates: {str(e)}"}


def _get_maps_api_key() -> str:
    """Reads GOOGLE_MAPS_API_KEY from environment or local .env file."""
    import os
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GOOGLE_MAPS_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key or ""


def geocode_address(address: str) -> dict:
    """Converts a street address or location name into geographic latitude/longitude coordinates using Google Geocoding API.

    Args:
        address: The street address, city, or location to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'Wall Street, NY').

    Returns:
        A dictionary containing formatted address, location coordinates (latitude, longitude), and place ID.
    """
    import json
    import urllib.parse
    import urllib.request

    key = _get_maps_api_key()
    if not key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "OK" or not data.get("results"):
            return {"error": f"Geocoding failed for address '{address}': {data.get('status')}"}

        result = data["results"][0]
        location = result["geometry"]["location"]

        return {
            "address": result.get("formatted_address", address),
            "location": {
                "latitude": location["lat"],
                "longitude": location["lng"]
            },
            "place_id": result.get("place_id", "")
        }
    except Exception as e:
        return {"error": f"Geocoding error: {str(e)}"}


def find_nearby_places(latitude: float, longitude: float, place_type: str = "bank", radius: float = 2000.0) -> list[dict]:
    """Finds nearby places of a specific type (e.g. 'bank', 'ATM', 'financial_advisor', 'accounting') near given coordinates using Places API (New).

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Type of place to search for (e.g. 'bank', 'ATM', 'accounting', 'law_firm'). Default is 'bank'.
        radius: Radius in meters around the center location (default: 2000.0).

    Returns:
        A list of dictionaries containing name, address, and location for each matching nearby place.
    """
    import json
    import urllib.request

    key = _get_maps_api_key()
    if not key:
        return [{"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}]

    places_url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
    }

    body_data = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude)
                },
                "radius": float(radius)
            }
        }
    }

    try:
        encoded_body = json.dumps(body_data).encode("utf-8")
        req = urllib.request.Request(places_url, data=encoded_body, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        raw_places = data.get("places", [])
        results = []

        for p in raw_places:
            display_name = p.get("displayName", {}).get("text", "Unknown")
            address = p.get("formattedAddress", "")
            loc = p.get("location", {})

            results.append({
                "name": display_name,
                "address": address,
                "location": {
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude")
                }
            })

        return results
    except Exception as e:
        return [{"error": f"Failed to search nearby places: {str(e)}"}]


def generate_milestone_graphic(tool_context: ToolContext, goal_name: str, milestone_text: str = "Financial Goal Achieved") -> dict:
    """Generates a visual financial milestone graphic or badge for an investment goal using gemini-3.1-flash-lite-image.

    Saves the image artifact to the Playground Artifacts panel and uploads it directly to Cloud Storage.

    Args:
        tool_context: ADK ToolContext injected automatically by the framework.
        goal_name: Name of the financial goal or milestone (e.g. 'Retirement Fund', 'First $100k Saved', 'Emergency Fund').
        milestone_text: Subtitle or milestone target description (e.g. '$100,000 Milestone', 'Goal Reached').

    Returns:
        A dictionary with the public Cloud Storage HTTPS URL of the generated image and the saved artifact filename.
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage
    from google.adk.tools import ToolContext

    bucket_name = "smart-wealth-assets-549c7ea1"
    prompt = f"A sleek, modern financial milestone badge graphic for '{goal_name}' with subtitle '{milestone_text}'. High quality, gold and emerald visual theme, clean vector design."

    # Call Gemini 3.1 Flash-Lite Image model in global region
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global"
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=[types.Modality.IMAGE]
        )
    )

    image_bytes = None
    mime_type = "image/png"
    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not image_bytes:
        return {"error": "Failed to generate image from model."}

    file_id = str(uuid.uuid4())[:8]
    filename = f"milestone_{file_id}.png"

    # 1. Save with tool_context.save_artifact
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload same image bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"

    return {
        "status": "success",
        "goal_name": goal_name,
        "artifact_filename": filename,
        "public_image_url": public_url
    }


def generate_wealth_video(tool_context: ToolContext, topic_or_prompt: str) -> dict:
    """Generates a short animated video or motion graphic for a financial concept, wealth goal, or investment visualization using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the video artifact to the Playground Artifacts panel and uploads it directly to Cloud Storage.

    Args:
        tool_context: ADK ToolContext injected automatically by the framework.
        topic_or_prompt: Description or topic for the financial video (e.g. 'Stock market growth chart', 'Compound interest wealth growth', 'Real estate investment milestone').

    Returns:
        A dictionary containing the public Cloud Storage HTTPS URL of the generated video and the saved artifact filename.
    """
    import base64
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage
    from google.adk.tools import ToolContext

    bucket_name = "smart-wealth-assets-549c7ea1"
    prompt = f"A sleek, professional animated financial video showing: {topic_or_prompt}. High quality gold and emerald wealth theme."

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global"
    )

    response = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt
    )

    if not hasattr(response, "output_video") or not response.output_video or not response.output_video.data:
        return {"error": "Failed to generate video from gemini-omni-flash-preview model."}

    # Extract video bytes from base64 data
    video_bytes = base64.b64decode(response.output_video.data)
    mime_type = getattr(response.output_video, "mime_type", None) or "video/mp4"

    file_id = str(uuid.uuid4())[:8]
    filename = f"wealth_video_{file_id}.mp4"

    # 1. Save artifact to Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload video bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"

    return {
        "status": "success",
        "topic": topic_or_prompt,
        "artifact_filename": filename,
        "public_video_url": public_url
    }


import json
import os
from google.adk.code_executors import AgentEngineSandboxCodeExecutor

# Load Agent Engine resource name from deployment_metadata.json
metadata_file = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
agent_engine_resource_name = None
if os.path.exists(metadata_file):
    with open(metadata_file, "r") as f:
        meta_data = json.load(f)
        agent_engine_resource_name = meta_data.get("remote_agent_runtime_id")

code_executor = None
if agent_engine_resource_name:
    code_executor = AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name=agent_engine_resource_name
    )


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_prompt = schema_manager.generate_system_prompt(
    role_description="You are Smart Wealth Concierge, a helpful personal finance and investment assistant. You help users track investment holdings, log expenses, check stock quotes, fetch real-time market news, calculate growth projections, convert currency rates, geocode addresses, locate nearby financial branches, and generate visual goal milestone graphics.",
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

agent_instruction = f"""{a2ui_prompt}

You remember user preferences and facts across conversations using your Memory Bank, specifically including all user base locations (home city, country, address) and preferred base currencies (e.g. USD, EUR, GBP, JPY, CAD, AUD). Whenever the user mentions or sets their location or default currency, remember it in Memory Bank and automatically apply it for future currency conversions, local market news, and nearby branch searches.
You also have code execution capability via a secure Python sandbox when complex computations or data manipulation are required.
Always use your tools, memory, or code execution sandbox to provide accurate data."""


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=agent_instruction,
    tools=[
        PreloadMemoryTool(),
        get_portfolio,
        add_or_update_holding,
        get_transactions,
        log_transaction,
        get_stock_quote,
        fetch_market_news,
        calculate_financial_projection,
        get_currency_exchange_rates,
        geocode_address,
        find_nearby_places,
        generate_milestone_graphic,
        generate_wealth_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    code_executor=code_executor,
)



app = App(
    root_agent=root_agent,
    name="app",
)







