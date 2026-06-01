import {
  Body,
  Controller,
  Get,
  Inject,
  Post,
  Req,
  UseGuards,
} from "@nestjs/common";
import { IsEmail, IsString, MinLength } from "class-validator";
import { AuthResponse, UserMeResponse } from "@personal-finances/contracts";

import { JwtAuthGuard } from "./guards/jwt-auth.guard.js";
import { AuthService } from "./auth.service.js";

class LoginRequestDto {
  @IsEmail()
  email!: string;

  @IsString()
  @MinLength(8)
  password!: string;
}

class RegisterRequestDto {
  @IsEmail()
  email!: string;

  @IsString()
  @MinLength(8)
  password!: string;
}

@Controller("auth")
export class AuthController {
  constructor(@Inject(AuthService) private readonly authService: AuthService) {}

  @Post("register")
  register(@Body() payload: RegisterRequestDto): Promise<AuthResponse> {
    return this.authService.register(
      payload.email.toLowerCase(),
      payload.password,
    );
  }

  @Post("login")
  login(@Body() payload: LoginRequestDto): Promise<AuthResponse> {
    return this.authService.login(
      payload.email.toLowerCase(),
      payload.password,
    );
  }

  @Get("me")
  @UseGuards(JwtAuthGuard)
  me(@Req() request: { user: { sub: string } }): Promise<UserMeResponse> {
    return this.authService.me(request.user.sub);
  }
}
