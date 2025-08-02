# Football Prop Insights - Step 1 Setup Guide

## Prerequisites

- Python 3.11+ installed on your system
- Git (for version control)

## Environment Setup

### 1. Install Dependencies

First, install the required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- `requests` - For making HTTP API calls
- `python-dotenv` - For environment variable management

### 2. Configure Environment Variables

#### Option A: Copy from Example File
1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` file with your actual API keys:
   ```bash
   # Open in your preferred text editor
   nano .env
   # or
   vim .env
   # or
   code .env
   ```

#### Option B: Create .env File Manually
Create a `.env` file in the project root with the following format:

```bash
# API Keys for Football Prop Insights - Step 1
# RapidAPI Configuration (for NFL Player Stats)
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=nfl-api-data.p.rapidapi.com

# College Football Data API
CFB_API_KEY=your_cfb_api_key_here

# Note: PrizePicks and Underdog Fantasy APIs do not require authentication
```

### 3. API Key Requirements

#### RapidAPI (NFL Player Stats)
- **Required**: `RAPIDAPI_KEY` and `RAPIDAPI_HOST`
- **Get your key**: Sign up at [RapidAPI.com](https://rapidapi.com)
- **Subscribe to**: NFL API Data by creativesdev
- **Rate limit**: 5,000 requests per day

#### College Football Data API
- **Required**: `CFB_API_KEY`
- **Get your key**: Sign up at [CollegeFootballData.com](https://collegefootballdata.com)
- **Rate limit**: 1,000 requests per month (free tier)

#### PrizePicks & Underdog Fantasy
- **No authentication required** - these APIs are publicly accessible

### 4. Verify Setup

Test your environment setup by running:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ Environment loaded successfully')"
```

To verify your API keys are loaded:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('RAPIDAPI_KEY:', 'SET' if os.getenv('RAPIDAPI_KEY') else 'MISSING'); print('CFB_API_KEY:', 'SET' if os.getenv('CFB_API_KEY') else 'MISSING')"
```

## Security Notes

- **Never commit** your `.env` file to version control
- The `.env` file is automatically ignored by Git (see `.gitignore`)
- Keep your API keys private and secure
- Rotate keys periodically for security

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment variables not loading**
   - Ensure `.env` file is in the project root directory
   - Check file permissions: `chmod 644 .env`
   - Verify no extra spaces in variable assignments

3. **API key format issues**
   - RapidAPI keys are typically 50+ characters long
   - CFB API keys contain special characters (+, /, =)
   - Ensure no quotes around the key values in `.env`

4. **Rate limit warnings**
   - NFL API: 5,000/day limit is generous for development
   - CFB API: 1,000/month limit - use sparingly during testing

## Next Steps

Once setup is complete, you can run the API connectivity tests:

```bash
python src/api_client.py
```

This will test all four API integrations and display sample data from each source.

---

**Support**: If you encounter issues, check the error messages carefully - they often indicate missing environment variables or network connectivity problems.