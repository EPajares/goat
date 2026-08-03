import type { Theme } from '@mui/material/styles'

const Switch = (theme: Theme) => {
  return {
    MuiSwitch: {
      styleOverrides: {
        root: {
          '& .MuiSwitch-track': {
            backgroundColor: theme.palette.customColors.main
          }
        }
      }
    }
  }
}

export default Switch
