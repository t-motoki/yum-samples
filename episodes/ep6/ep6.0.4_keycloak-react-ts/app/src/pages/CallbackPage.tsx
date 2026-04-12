import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, CircularProgress, Typography } from '@mui/material'
import { userManager } from '../auth/oidcConfig'

export default function CallbackPage() {
  const navigate = useNavigate()

  useEffect(() => {
    // Keycloak からのリダイレクト（認証コード）を処理してトークンに交換する
    userManager
      .signinRedirectCallback()
      .then(() => {
        navigate('/profile')
      })
      .catch((err) => {
        console.error('callback error:', err)
        navigate('/')
      })
  }, [navigate])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 10 }}>
      <CircularProgress />
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        認証処理中...
      </Typography>
    </Box>
  )
}
