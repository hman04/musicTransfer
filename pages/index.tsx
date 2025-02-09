import {
  Box,
  Container,
  Heading,
  VStack,
  Input,
  Button,
  Text,
  useToast,
  Progress,
  Flex,
  Icon,
  Badge,
  Image,
} from '@chakra-ui/react'
import { useState } from 'react'
import { FaSpotify, FaYoutube, FaMusic } from 'react-icons/fa'

export default function Home() {
  const [spotifyUrl, setSpotifyUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const toast = useToast()

  const handlePreview = async () => {
    if (!spotifyUrl.includes('spotify.com/playlist/')) {
      toast({
        title: 'Invalid URL',
        description: 'Please enter a valid Spotify playlist URL',
        status: 'error',
        duration: 3000,
      })
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch('https://musictransfer.onrender.com/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `spotify_url=${encodeURIComponent(spotifyUrl)}`
      })
      const data = await response.json()
      
      toast({
        title: 'Preview Ready',
        description: `Found ${data.total_tracks} tracks`,
        status: 'success',
        duration: 5000,
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to preview playlist',
        status: 'error',
      })
    }
    setIsLoading(false)
  }

  const handleTransfer = async () => {
    if (!spotifyUrl.includes('spotify.com/playlist/')) {
      toast({
        title: 'Invalid URL',
        description: 'Please enter a valid Spotify playlist URL',
        status: 'error',
        duration: 3000,
      })
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch('https://musictransfer.onrender.com/create_playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `spotify_url=${encodeURIComponent(spotifyUrl)}`
      })
      
      const data = await response.json()
      
      if (data.redirect) {
        window.location.href = 'https://musictransfer.onrender.com' + data.redirect
        return
      }
      
      toast({
        title: 'Transfer Started',
        description: 'Your playlist is being created',
        status: 'success',
        duration: 5000,
      })
      
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Transfer failed',
        status: 'error',
      })
    }
    setIsLoading(false)
  }

  return (
    <Box minH="100vh" py={20} bg="gray.50">
      <Container maxW="container.md">
        <VStack spacing={8}>
          {/* Header */}
          <Flex align="center" gap={4}>
            <Icon as={FaSpotify} w={8} h={8} color="green.500" />
            <Icon as={FaMusic} w={6} h={6} color="purple.500" />
            <Icon as={FaYoutube} w={8} h={8} color="red.500" />
          </Flex>
          
          <Heading
            fontSize={{ base: "3xl", md: "4xl" }}
            bgGradient="linear(to-r, green.400, purple.500, red.400)"
            bgClip="text"
            textAlign="center"
          >
            Transfer Your Music
          </Heading>
          
          <Text fontSize="lg" color="gray.600" textAlign="center">
            Move your playlists from Spotify to YouTube Music in seconds
          </Text>

          {/* Main Form */}
          <Box
            w="full"
            bg="white"
            p={8}
            borderRadius="xl"
            boxShadow="xl"
            border="1px"
            borderColor="gray.100"
          >
            <VStack spacing={6}>
              <Input
                value={spotifyUrl}
                onChange={(e) => setSpotifyUrl(e.target.value)}
                placeholder="Paste Spotify playlist URL"
                size="lg"
                borderRadius="lg"
              />

              <Button
                onClick={handlePreview}
                colorScheme="purple"
                size="lg"
                w="full"
                isLoading={isLoading}
                loadingText="Previewing..."
                leftIcon={<FaSpotify />}
              >
                Preview Transfer
              </Button>

              {progress > 0 && (
                <Box w="full">
                  <Progress
                    value={progress}
                    colorScheme="green"
                    hasStripe
                    isAnimated
                    borderRadius="lg"
                    height="4px"
                  />
                  <Text mt={2} textAlign="center" color="gray.600">
                    Transferring... {Math.round(progress)}%
                  </Text>
                </Box>
              )}

              <Button
                onClick={handleTransfer}
                colorScheme="green"
                size="lg"
                w="full"
                isDisabled={!spotifyUrl || isLoading}
                leftIcon={<FaYoutube />}
              >
                Start Transfer
              </Button>
            </VStack>
          </Box>

          {/* Features */}
          <Flex wrap="wrap" gap={4} justify="center">
            {['Lightning Fast', 'Free to Use', 'Simple & Easy'].map((feature) => (
              <Badge
                key={feature}
                px={4}
                py={2}
                borderRadius="full"
                colorScheme="purple"
                fontSize="md"
              >
                {feature}
              </Badge>
            ))}
          </Flex>
        </VStack>
      </Container>
    </Box>
  )
} 