# pswd

## Whoami

**pswd** is a CLI password manager that keeps
data on users device via RSA encryption.

### Example

```shell
$ pswd new "steam" "p3n5G4QBbm:-L!C"
$ pswd get "steam"  
p3n5G4QBbm:-L!C

$ pswd get "StEaM"
p3n5G4QBbm:-L!C

$ pswd copy "steam"
$ pswd edit "steam" "._C7nq!6kzWDvDV"
$ pswd new "instagram" "smart_password"
$ pswd view-keys
steam
instagram

$ pswd view-passwords
steam            ._C7nq!6kzWDvDV
instagram        smart_password

$ pswd delete "instagram"
```

## Install

1. Download the latest version from [releases](https://github.com/s1cklove/pswd/releases)
and unpack it
2. Based on OS, pip required:
- **Windows**: run command line (or PowerShell)
as admin, go to root project directory and
type `pip install .`.
- **Linux/Mac OS**: get to project root directory
in command line and type `sudo pip install .`.
