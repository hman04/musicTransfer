'use client'

import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  Input,
  Button,
  Icon,
  HStack,
  Progress,
  Card,
  CardBody,
  useToast,
} from '@chakra-ui/react'
import { useState } from 'react'
import { FaSpotify, FaYoutube } from 'react-icons/fa'

const BACKEND_URL = process.env.NODE_ENV === 'production' 
  ? 'https://musictransfer.onrender.com' 
  : 'http://localhost:5001'

export default function Home() {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const toast = useToast()

  const handleTransfer = async () => {
    if (!url.includes('spotify.com/playlist/')) {
      toast({
        title: 'Invalid URL',
        description: 'Please enter a valid Spotify playlist URL',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${BACKEND_URL}/transfer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `spotify_url=${encodeURIComponent(url)}`
      })
      const data = await response.json()
      
      if (data.error) {
        throw new Error(data.error)
      }

      toast({
        title: 'Transfer Started',
        description: `Found ${data.total_tracks} tracks to transfer`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to start transfer',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
    setIsLoading(false)
  }

  return (
    <Box minH="100vh" py={20} bg="gray.50">
      <Container maxW="container.md">
        <VStack spacing={8}>
          {/* Header */}
          <HStack spacing={4}>
            <Icon as={FaSpotify} w={10} h={10} color="green.500" />
            <Icon as={FaYoutube} w={10} h={10} color="red.500" />
          </HStack>

          <VStack spacing={2}>
            <Heading 
              size="2xl"
              bgGradient="linear(to-r, green.400, red.400)"
              bgClip="text"
            >
              Music Transfer
            </Heading>
            <Text color="gray.600" fontSize="lg">
              Transfer your playlists from Spotify to YouTube Music
            </Text>
          </VStack>

          {/* Main Card */}
          <Card w="full" variant="filled" shadow="lg">
            <CardBody>
              <VStack spacing={4}>
                <Input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Paste Spotify playlist URL"
                  size="lg"
                  variant="filled"
                />

                <Button
                  onClick={handleTransfer}
                  colorScheme="green"
                  size="lg"
                  width="full"
                  isLoading={isLoading}
                  loadingText="Starting Transfer..."
                  leftIcon={<Icon as={FaSpotify} />}
                >
                  Start Transfer
                </Button>

                {progress > 0 && (
                  <Progress
                    value={progress}
                    width="100%"
                    colorScheme="green"
                    hasStripe
                    isAnimated
                  />
                )}
              </VStack>
            </CardBody>
          </Card>
        </VStack>
      </Container>
    </Box>
  )
}
