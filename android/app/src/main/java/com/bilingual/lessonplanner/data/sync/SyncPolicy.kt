package com.bilingual.lessonplanner.data.sync

enum class NetworkType {
    WIFI,
    MOBILE,
    NONE
}

enum class SyncType {
    FULL,
    INCREMENTAL,
    CRITICAL
}

data class SyncPolicy(
    val networkType: NetworkType,
    val syncType: SyncType,
    val allowFullSync: Boolean,
    val allowIncrementalSync: Boolean,
    val allowCriticalSync: Boolean
) {
    companion object {
        fun forNetwork(networkType: NetworkType): SyncPolicy {
            return when (networkType) {
                NetworkType.WIFI -> SyncPolicy(
                    networkType = NetworkType.WIFI,
                    syncType = SyncType.FULL,
                    allowFullSync = true,
                    allowIncrementalSync = true,
                    allowCriticalSync = true
                )
                NetworkType.MOBILE -> SyncPolicy(
                    networkType = NetworkType.MOBILE,
                    syncType = SyncType.INCREMENTAL,
                    allowFullSync = false,
                    allowIncrementalSync = true,
                    allowCriticalSync = true
                )
                NetworkType.NONE -> SyncPolicy(
                    networkType = NetworkType.NONE,
                    syncType = SyncType.CRITICAL,
                    allowFullSync = false,
                    allowIncrementalSync = false,
                    allowCriticalSync = false
                )
            }
        }
    }
}

