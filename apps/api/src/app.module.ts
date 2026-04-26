import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";

import { AppController } from "./app.controller.js";
import { AppService } from "./app.service.js";
import { AuthModule } from "./auth/auth.module.js";
import { FinanceModule } from "./finance/finance.module.js";
import { PlaidModule } from "./plaid/plaid.module.js";
import { PrismaModule } from "./common/prisma.module.js";
import { SyncModule } from "./sync/sync.module.js";
import { validateEnv } from "./common/env.validation.js";

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true, validate: validateEnv }),
    PrismaModule,
    AuthModule,
    PlaidModule,
    FinanceModule,
    SyncModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
