# SwipeClock Integration

Import SwipeClock timecard data as attendances for each hourly employee.

API documentation can be found here:

https://twpapi.payrollservers.us/swagger/ui/index#!/TimeCards/TimeCards_GetTimeCards

## Configuration

- Authorization URL: https://clock.payrollservers.us/AuthenticationService/oauth2/usertoken
- API URL: https://twpapi.payrollservers.us
- Site ID (5 digit number)
- API Secret Key (64 random characters)

## Testing

You can inspect the generated JWT (JSON Web Token) at jwt.io.

Remember that JWTs have an expiration time.  If the clock on the server is slow, you may
get an Invalid Signature error.
