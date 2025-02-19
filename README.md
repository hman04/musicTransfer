# YouTube Music Playlist Transfer Tool

A web application that allows users to transfer playlists from Spotify to YouTube Music. Built with FastAPI backend and Next.js frontend.

## Features
- OAuth2 authentication with YouTube Music
- Spotify playlist URL parsing and preview 
- Batch processing of song transfers
- Real-time transfer progress updates via WebSocket
- Rate limiting protection
- Secure credential handling

## Prerequisites
- Python 3.13+
- Node.js
- YouTube Music API credentials
- Spotify API access

## Setup
1. Clone the repository:
   bash
git clone <repository-url>
cd <project-directory>
2. Set up the backend:
   bash
Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate
Install dependencies
pip install -r requirements.txt
Create .env file and add your credentials
touch .env

3. Add the following to your `.env` file:

GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
4. Set up the frontend:

bash
cd frontend
npm install

## Running the Application
1. Start the backend server:

bash
cd backend
uvicorn app.main:app --reload

2. Start the frontend development server:

bash
cd frontend
npm run dev
3. Access the application at `http://localhost:3000`

## API Endpoints
- `GET /api/auth/login` - Initiate YouTube Music authentication
- `GET /api/auth/callback` - Handle OAuth callback
- `POST /api/preview` - Preview Spotify playlist
- `POST /api/transfer` - Start playlist transfer
- `GET /api/status/{transfer_id}` - Check transfer status
- `WS /ws/{transfer_id}` - WebSocket for real-time updates

## Security
- Environment variables for sensitive credentials
- CORS protection
- Rate limiting
- Secure cookie handling
- OAuth2 authentication

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License

## Acknowledgments
- YouTube Music API
- Spotify API
- FastAPI
- Next.js

## Contact
For any questions or issues, please open an issue on GitHub.
