import { Injectable, UnauthorizedException } from "@nestjs/common";
import { AuthGuard } from "@nestjs/passport";

@Injectable()
export class JwtAuthGuard extends AuthGuard("jwt") {
  handleRequest<TUser extends { mfa?: string }>(
    err: unknown,
    user: TUser | false | null,
  ): TUser {
    if (err || !user) {
      throw err ?? new UnauthorizedException();
    }

    // Only allow fully authenticated sessions to access protected resources.
    // Backward compatible: if token lacks mfa claim, treat as verified.
    if (user.mfa && user.mfa !== "verified") {
      throw new UnauthorizedException("MFA verification required");
    }

    return user;
  }
}
