import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import React from 'react'
import { Providers } from './providers'

const geist = Geist({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Music Transfer",
  description: "Transfer your playlists from Spotify to YouTube Music",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={geist.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}