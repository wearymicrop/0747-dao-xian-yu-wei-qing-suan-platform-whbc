# 岛线余位清算台深度登记

南埠值航员在发船前复核退票、换票和候补释放，按船班和层级对平席位。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 船班档期 | 认定办理与停退时间 | `GET /api/sailings/{source}` | `app/modules/m1_sailings/windows.py` | `tests/test_sailings.py` |
| M2 席位层级 | 核对各船席位与资格 | `GET /api/seats/{source}` | `app/modules/m2_seats/contract.py` | `tests/test_seats.py` |
| M3 订单采集 | 检查回传重复与流水冲突 | `GET /api/orders/{source}` | `app/modules/m3_orders/service.py` | `tests/test_orders.py` |
| M4 换票链路 | 确认原票及新席变化 | `GET /api/transfers/{source}` | `app/modules/m4_transfers/service.py` | `tests/test_transfers.py` |
| M5 候补递补 | 核查同层排队与释放 | `GET /api/waitlist/{source}` | `app/modules/m5_waitlist/service.py` | `tests/test_waitlist.py` |
| M6 余位对账 | 检查每一层级容量守恒 | `GET /api/reconcile/{source}` | `app/modules/m6_reconcile/service.py` | `tests/test_reconcile.py` |
| M7 值航留档 | 保存值航结果并下载凭证 | `POST /api/runs` | `app/modules/m7_archive/signoff.py` `app/modules/m7_archive/service.py` | `tests/test_archive.py` `tests/test_bundle.py` |

## 陷阱登记

| TRAP | 现象 | 朴素实现 | 处理 | 位置 | 测试 |
|---|---|---|---|---|---|
| TRAP-08 | 订单号有前导零 | 数字化丢零 | 保留字符串 | `app/modules/m3_orders/events.py` | `tests/test_orders.py::test_old_event_is_reordered_and_zeros_preserved` |
| TRAP-11 | 同回传不同偏移 | 错当新订单 | 时间先归一 | `app/modules/m3_orders/service.py` | `tests/test_orders.py::test_identical_events_with_different_offsets_merge` |
| TRAP-13 | 停退后回传早先退款 | 误放座 | 退票按收到时间裁决 | `app/modules/m4_transfers/service.py` | `tests/test_transfers.py::test_received_late_refund_never_releases` |
| TRAP-14 | 支付流水关联多单 | 后到覆盖 | 整组隔离 | `app/modules/m3_orders/service.py` | `tests/test_orders.py::test_payment_used_on_other_order_quarantined` |
| TRAP-19 | 普通候补先于轮椅 | 阻塞专席 | 资格通过才入可递补队列 | `app/modules/m5_waitlist/service.py` | `tests/test_waitlist.py::test_ineligible_does_not_block_restricted_queue` |
| TRAP-20 | 同席自换 | 错误释放 | 拒绝自换 | `app/modules/m4_transfers/service.py` | `tests/test_transfers.py::test_same_seat_swap_rejected` |
| TRAP-23 | 到期释放早于查询 | 递补时间晚记 | 在到期时点补发 | `app/modules/m4_transfers/service.py` | `tests/test_waitlist.py::test_expiration_promotes_at_expiry_not_later` |
| TRAP-25 | 同船班定义冲突 | 任取一条 | 隔离同编号档期 | `app/modules/m1_sailings/service.py` | `tests/test_sailings.py::test_overlapping_sailing_id_conflicting` |
| TRAP-26 | 改签后引用旧票 | 二次释放或撤销新票 | 校验当前有效票 | `app/modules/m4_transfers/tickets.py` | `tests/test_transfers.py::test_stale_ticket_rejected` |

## 对账

脏样例共 21 席，清算为出台票 18、保留 2、开放 1。原始回传、执行与隔离另记行账。
