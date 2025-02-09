import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const response = await fetch('https://musictransfer.onrender.com/transfer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `spotify_url=${encodeURIComponent(req.body.spotify_url)}`
  })
  
  const data = await response.json()
  res.status(200).json(data)
} 