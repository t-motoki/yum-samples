import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Typography,
} from '@mui/material'
import AccountCircleIcon from '@mui/icons-material/AccountCircle'
import { Link } from 'react-router-dom'
import type { KeycloakProfile } from '../auth/types'

interface Props {
  profile: KeycloakProfile | null
  onLogout: () => void
}

export default function ProfileCard({ profile, onLogout }: Props) {
  if (!profile) return null

  // 主要クレームを先頭に、それ以外をその後に並べる
  const primaryKeys = ['sub', 'preferred_username', 'email', 'name', 'given_name', 'family_name', 'email_verified']
  const otherKeys = Object.keys(profile).filter((k) => !primaryKeys.includes(k))
  const orderedEntries = [
    ...primaryKeys.filter((k) => k in profile).map((k) => [k, profile[k]] as [string, unknown]),
    ...otherKeys.map((k) => [k, profile[k]] as [string, unknown]),
  ]

  return (
    <Card elevation={3}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56, mr: 2 }}>
            <AccountCircleIcon sx={{ fontSize: 40 }} />
          </Avatar>
          <Box>
            <Typography variant="h6">
              {profile.name ?? profile.preferred_username}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {profile.email}
            </Typography>
          </Box>
          {profile.email_verified && (
            <Chip label="認証済み" color="success" size="small" sx={{ ml: 'auto' }} />
          )}
        </Box>

        <Divider sx={{ mb: 2 }} />

        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          クレーム一覧
        </Typography>
        <Table size="small">
          <TableBody>
            {orderedEntries.map(([key, value]) => (
              <TableRow key={key}>
                <TableCell sx={{ fontWeight: 'bold', width: '40%', wordBreak: 'break-all' }}>
                  {key}
                </TableCell>
                <TableCell sx={{ wordBreak: 'break-all' }}>
                  {String(value)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
          {/* href ではなく component={Link} で SPA ルーティングを経由する */}
          <Button variant="outlined" component={Link} to="/" size="small">
            トップへ
          </Button>
          <Button variant="outlined" color="error" onClick={onLogout} size="small">
            ログアウト
          </Button>
        </Box>
      </CardContent>
    </Card>
  )
}
