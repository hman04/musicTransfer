import React from 'react'
import type { AppProps } from 'next/dist/shared/lib/router/app'
import { ChakraProvider } from '@chakra-ui/react'
import { extendTheme } from '@chakra-ui/theme-utils'

const theme = extendTheme({
  colors: {
    brand: {
      50: '#f5f3ff',
      100: '#ede9fe',
      500: '#8b5cf6',
      600: '#7c3aed',
      700: '#6d28d9',
    },
  },
  styles: {
    global: {
      body: {
        bg: 'gray.50',
      },
    },
  },
})

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ChakraProvider theme={theme}>
      <Component {...pageProps} />
    </ChakraProvider>
  )
} 