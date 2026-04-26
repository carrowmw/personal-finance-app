import { Injectable } from "@nestjs/common";
import { AuthGuard } from "@nestjs/passport";

// Allows any valid JWT (including MFA setup/pending tokens).
@Injectable()
export class JwtPreAuthGuard extends AuthGuard("jwt") {}
