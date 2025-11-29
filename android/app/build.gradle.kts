plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.dagger.hilt.android")
    kotlin("kapt")
    kotlin("plugin.serialization") version "1.9.20"
}

import java.util.Properties
import java.io.FileInputStream

// Load local.properties for Supabase configuration
val localProperties = Properties()
val localPropertiesFile = rootProject.file("local.properties")
if (localPropertiesFile.exists()) {
    FileInputStream(localPropertiesFile).use { localProperties.load(it) }
}

// Also try app-level local.properties
val appLocalPropertiesFile = file("local.properties")
if (appLocalPropertiesFile.exists()) {
    FileInputStream(appLocalPropertiesFile).use { localProperties.load(it) }
}

android {
    namespace = "com.bilingual.lessonplanner"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.bilingual.lessonplanner"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }
        
        // Supabase configuration from local.properties or environment
        buildConfigField(
            "String",
            "SUPABASE_URL_PROJECT1",
            "\"${localProperties.getProperty("SUPABASE_URL_PROJECT1", "")}\""
        )
        buildConfigField(
            "String",
            "SUPABASE_KEY_PROJECT1",
            "\"${localProperties.getProperty("SUPABASE_KEY_PROJECT1", "")}\""
        )
        buildConfigField(
            "String",
            "SUPABASE_URL_PROJECT2",
            "\"${localProperties.getProperty("SUPABASE_URL_PROJECT2", "")}\""
        )
        buildConfigField(
            "String",
            "SUPABASE_KEY_PROJECT2",
            "\"${localProperties.getProperty("SUPABASE_KEY_PROJECT2", "")}\""
        )
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    
    kotlinOptions {
        jvmTarget = "17"
    }
    
    // KAPT configuration for Java 21 compatibility
    kapt {
        javacOptions {
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED")
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED")
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED")
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED")
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.jvm=ALL-UNNAMED")
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED")
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED")
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.processing=ALL-UNNAMED")
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED")
            option("--add-opens", "jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED")
        }
    }
    
    buildFeatures {
        compose = true
        buildConfig = true
    }
    
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.4"
    }
    
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // Core Android
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.6.2")
    implementation("androidx.activity:activity-compose:1.8.1")
    
    // Compose
    implementation(platform("androidx.compose:compose-bom:2024.06.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    
    // Navigation
    implementation("androidx.navigation:navigation-compose:2.7.5")
    
    // Hilt
    implementation("com.google.dagger:hilt-android:2.48")
    kapt("com.google.dagger:hilt-android-compiler:2.48")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")
    
    // Room
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // DataStore
    implementation("androidx.datastore:datastore-preferences:1.0.0")
    
    // WorkManager
    implementation("androidx.work:work-runtime-ktx:2.9.0")
    implementation("androidx.hilt:hilt-work:1.1.0")
    kapt("androidx.hilt:hilt-compiler:1.1.0")
    
    // Supabase
    implementation(platform("io.github.jan-tennert.supabase:bom:2.0.0"))
    implementation("io.github.jan-tennert.supabase:postgrest-kt")
    implementation("io.github.jan-tennert.supabase:realtime-kt")
    implementation("io.ktor:ktor-client-android:2.3.5")
    
    // Kotlinx Serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")
    
    // Testing
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2024.06.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}

